import os
import uuid

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from helpers import CURRENCY_OPTIONS
from models import AppSettings, Gift, db


items_bp = Blueprint("items", __name__, url_prefix="/api")


# ============================================================
# Image storage
# ============================================================

# This is the path INSIDE the Docker container.
# Docker Compose maps the host directory to this location.
IMAGE_STORAGE = "/app/uploads"

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
}


def save_uploaded_image(file):
    """
    Save an uploaded image to the local image storage.

    Returns the URL that should be stored in Gift.image_url.
    """

    if not file or not file.filename:
        return None

    original_filename = secure_filename(file.filename)

    if not original_filename:
        raise ValueError("Invalid image filename")

    if "." not in original_filename:
        raise ValueError("Image must have a file extension")

    extension = original_filename.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Unsupported image type. "
            "Use JPG, JPEG, PNG, WebP, or GIF."
        )

    gifts_dir = os.path.join(
        IMAGE_STORAGE,
        "gifts",
    )

    os.makedirs(
        gifts_dir,
        exist_ok=True,
    )

    # Generate our own filename instead of trusting the
    # uploaded filename. This avoids collisions and unsafe names.
    filename = f"{uuid.uuid4().hex}.{extension}"

    file_path = os.path.join(
        gifts_dir,
        filename,
    )

    file.save(file_path)

    return f"/api/uploads/gifts/{filename}"

def delete_local_image(image_url):
    """
    Delete a locally uploaded gift image.

    External URLs are ignored.
    """
    if not image_url or not image_url.startswith("/api/uploads/gifts/"):
        return

    filename = os.path.basename(image_url)
    image_path = os.path.join(IMAGE_STORAGE, "gifts", filename)

    # Safety: only delete files that actually exist in our gift upload directory.
    if os.path.isfile(image_path):
        os.remove(image_path)
# ============================================================
# Claim management
# ============================================================

def claim_management_active():
    # A wishlist's own opt-in only takes effect while the admin
    # also allows the feature site-wide -- both gates are checked here.
    #
    # Governs the passive surface (claimed_count in the item list,
    # the lock icon, resetting claims) so simply browsing a wishlist
    # can't reveal which items are claimed without opting in.

    site_settings = AppSettings.query.get(1)

    return (
        current_user.claim_management_enabled
        and site_settings.claim_management_site_enabled
    )


def owner_gift_dict(gift):
    return gift.to_dict(
        include_claim_status=claim_management_active()
    )


# ============================================================
# Get items
# ============================================================

@items_bp.route("/items")
@login_required
def get_items():
    gifts = Gift.query.filter_by(
        owner_id=current_user.id
    ).all()

    return jsonify([
        owner_gift_dict(gift)
        for gift in gifts
    ])


# ============================================================
# Rating
# ============================================================

@items_bp.route(
    "/items/<int:item_id>/rating",
    methods=["PATCH"],
)
@login_required
def update_rating(item_id):
    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify({"error": "Not your item"}), 403

    data = request.get_json()

    gift.rating = data["rating"]

    # A rating change moves the item to a new group,
    # so drop its old manual position.
    gift.sort_order = None

    db.session.commit()

    return jsonify(
        owner_gift_dict(gift)
    )


# ============================================================
# Received
# ============================================================

@items_bp.route(
    "/items/<int:item_id>/received",
    methods=["PATCH"],
)
@login_required
def update_received(item_id):
    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify({"error": "Not your item"}), 403

    data = request.get_json()

    new_received = bool(
        data.get("received", True)
    )

    # Unlimited items never "run out".
    #
    # Receiving one round doesn't mean the owner is done wanting
    # more, so keep it on the active list and just clear existing
    # claims instead of archiving it.
    if gift.quantity is None and new_received:

        for claim in list(gift.claims):
            db.session.delete(claim)

        db.session.commit()

        return jsonify(
            owner_gift_dict(gift)
        )

    gift.received = new_received

    db.session.commit()

    return jsonify(
        owner_gift_dict(gift)
    )


# ============================================================
# Create item
# ============================================================

@items_bp.route(
    "/items",
    methods=["POST"],
)
@login_required
def create_item():

    # --------------------------------------------------------
    # Support both:
    #
    # 1. application/json
    # 2. multipart/form-data
    #
    # This keeps the existing API working while allowing
    # actual image files to be uploaded.
    # --------------------------------------------------------

    if (
        request.content_type
        and request.content_type.startswith(
            "multipart/form-data"
        )
    ):
        data = request.form
        image_file = request.files.get("image")

    else:
        data = request.get_json() or {}
        image_file = None

    # --------------------------------------------------------
    # Currency validation
    # --------------------------------------------------------

    currency = data.get("currency")

    if (
        currency is not None
        and currency not in CURRENCY_OPTIONS
    ):
        return jsonify(
            {"error": "Invalid currency"}
        ), 400

    # --------------------------------------------------------
    # Image
    # --------------------------------------------------------

    image_url = data.get("image_url")

    if image_file:

        try:
            image_url = save_uploaded_image(
                image_file
            )

        except ValueError as exc:

            return jsonify(
                {"error": str(exc)}
            ), 400

    # --------------------------------------------------------
    # Create gift
    # --------------------------------------------------------

    gift = Gift(
        owner_id=current_user.id,
        title=data["title"],
        label=data.get("label"),
        brand=data.get("brand"),
        options=data.get("options"),
        url=data.get("url"),
        image_url=image_url,
        description=data.get("description"),
        price=data.get("price"),
        currency=currency,
        quantity=data.get("quantity", 1),
        rating=data.get("rating"),
    )

    db.session.add(gift)

    db.session.commit()

    return jsonify(
        owner_gift_dict(gift)
    ), 201


# ============================================================
# Update item
# ============================================================

@items_bp.route(
    "/items/<int:item_id>",
    methods=["PUT"],
)
@login_required
def update_item(item_id):
    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify(
            {"error": "Not your item"}
        ), 403

    # --------------------------------------------------------
    # Support JSON and multipart/form-data
    # --------------------------------------------------------

    if (
        request.content_type
        and request.content_type.startswith(
            "multipart/form-data"
        )
    ):
        data = request.form
        image_file = request.files.get("image")
    else:
        data = request.get_json() or {}
        image_file = None

    # --------------------------------------------------------
    # Image
    # --------------------------------------------------------

    old_image_url = gift.image_url

    remove_image = (
        str(data.get("remove_image", "")).lower()
        == "true"
    )

    if remove_image:
        delete_local_image(old_image_url)
        gift.image_url = None

    elif image_file:
        try:
            new_image_url = save_uploaded_image(
                image_file
            )

        except ValueError as exc:
            return jsonify(
                {"error": str(exc)}
            ), 400

        # If replacing a local image, remove the old one.
        delete_local_image(old_image_url)

        gift.image_url = new_image_url

    elif "image_url" in data:
        new_image_url = data.get("image_url")

        # If replacing/removing a local image through
        # image_url, clean up the old local file.
        if new_image_url != old_image_url:
            delete_local_image(old_image_url)

        gift.image_url = new_image_url

    # --------------------------------------------------------
    # Basic fields
    # --------------------------------------------------------

    gift.title = data.get(
        "title",
        gift.title,
    )

    gift.label = data.get(
        "label",
        gift.label,
    )

    gift.brand = data.get(
        "brand",
        gift.brand,
    )

    gift.options = data.get(
        "options",
        gift.options,
    )

    gift.url = data.get(
        "url",
        gift.url,
    )

    gift.description = data.get(
        "description",
        gift.description,
    )

    gift.price = data.get(
        "price",
        gift.price,
    )

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    if "currency" in data:

        new_currency = data["currency"]

        if (
            new_currency is not None
            and new_currency not in CURRENCY_OPTIONS
        ):
            return jsonify(
                {"error": "Invalid currency"}
            ), 400

        gift.currency = new_currency

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    gift.quantity = data.get(
        "quantity",
        gift.quantity,
    )

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    new_rating = data.get(
        "rating",
        gift.rating,
    )

    if new_rating != gift.rating:

        gift.sort_order = None

    gift.rating = new_rating

    # --------------------------------------------------------
    # Manual ordering
    # --------------------------------------------------------

    if "sort_order" in data:
        gift.sort_order = data["sort_order"]

    db.session.commit()

    return jsonify(
        owner_gift_dict(gift)
    )

# ============================================================
# Delete item
# ============================================================


@items_bp.route(
    "/items/<int:item_id>",
    methods=["DELETE"],
)
@login_required
def delete_item(item_id):
    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify(
            {"error": "Not your item"}
        ), 403

    # Delete locally stored image, if any.
    # External image URLs are ignored.
    delete_local_image(gift.image_url)

    db.session.delete(gift)

    db.session.commit()

    return "", 204
# ============================================================
# Claim info
# ============================================================

@items_bp.route(
    "/items/<int:item_id>/claim-info",
    methods=["GET"],
)
@login_required
def item_claim_info(item_id):

    # Count-only preflight for destructive owner actions.
    # Keeping names out of this response prevents it from bypassing
    # the wishlist's reveal opt-in.

    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify(
            {"error": "Not your item"}
        ), 403

    return jsonify({
        "claimed_count": len(gift.claims)
    })


# ============================================================
# View claims
# ============================================================

@items_bp.route(
    "/items/<int:item_id>/claims",
    methods=["GET"],
)
@login_required
def item_claims(item_id):

    # Unlike the passive surface gated by claim_management_active()
    # an owner can always deliberately reveal a name one at a time.

    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify(
            {"error": "Not your item"}
        ), 403

    return jsonify({
        "claimed_by": [
            claim.claimed_by
            for claim in gift.claims
        ]
    })


# ============================================================
# Reset claims
# ============================================================

@items_bp.route(
    "/items/<int:item_id>/claims",
    methods=["DELETE"],
)
@login_required
def reset_item_claims(item_id):

    gift = db.get_or_404(
        Gift,
        item_id,
    )

    if gift.owner_id != current_user.id:
        return jsonify(
            {"error": "Not your item"}
        ), 403

    if not claim_management_active():
        return jsonify({
            "error": (
                "Claim management is disabled "
                "for this wishlist"
            )
        }), 403

    for claim in list(gift.claims):
        db.session.delete(claim)

    db.session.commit()

    return jsonify(
        owner_gift_dict(gift)
    )
