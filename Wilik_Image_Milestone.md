# Wilik --- Image Milestone

**Status:** 🟡 In Progress

## Goal

Build a reliable local image system for Wilik where wishlist images are
uploaded, validated, optimized, stored on dedicated storage, served
correctly, and cleaned up when no longer needed.

------------------------------------------------------------------------

## 1. Current Features

-   [x] Local image upload
-   [x] External image URL support
-   [x] Image storage configurable through `.env`
-   [x] Store images outside the Docker container
-   [x] Store development images on Windows/WSL storage
-   [x] Serve uploaded images through `/api/uploads/...`
-   [x] Verify uploaded images are physically saved
-   [x] Verify uploaded images display correctly
-   [x] Preserve existing product-image scraping

------------------------------------------------------------------------

## 2. Upload Limits

-   [ ] Add maximum image/request size
-   [ ] Recommended maximum: **10 MB**
-   [ ] Add frontend file-size validation
-   [ ] Show a clear error when an image is too large

Example:

``` python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
```

------------------------------------------------------------------------

## 3. Image Validation

Current upload validation checks the file extension.

Improve this to validate the actual image.

-   [ ] Validate actual image contents
-   [ ] Reject renamed/non-image files
-   [ ] Allow:
    -   JPG
    -   JPEG
    -   PNG
    -   WebP
    -   GIF
-   [ ] Reject SVG
-   [ ] Never trust the original filename
-   [x] Generate server-side UUID filenames

------------------------------------------------------------------------

## 4. Image Processing

Use Pillow for image processing.

-   [ ] Add Pillow dependency
-   [ ] Open and validate uploaded image with Pillow
-   [ ] Resize excessively large images
-   [ ] Set a sensible maximum dimension
-   [ ] Convert uploaded images to WebP
-   [ ] Save normalized images as `.webp`
-   [ ] Optimize file size
-   [ ] Test image quality after conversion

Target flow:

``` text
Phone / Camera Image
        ↓
      Upload
        ↓
     Validate
        ↓
 Resize if needed
        ↓
   Convert WebP
        ↓
    Save image
```

Example target:

``` text
4–8 MB JPEG
      ↓
Wilik processing
      ↓
optimized WebP
      ↓
~200–600 KB
```

------------------------------------------------------------------------

## 5. Storage

### Development

Example:

``` env
WILIK_IMAGE_STORAGE=/mnt/c/Users/Orork/Desktop/tst
```

### Production

Example:

``` env
WILIK_IMAGE_STORAGE=/mnt/Bigdata/wilik/images
```

Docker mapping:

``` yaml
volumes:
  - ${WILIK_IMAGE_STORAGE}:/app/uploads
```

Container path:

``` text
/app/uploads
```

Database image URL:

``` text
/api/uploads/gifts/<uuid>.webp
```

Do **not** store the host filesystem path in the database.

------------------------------------------------------------------------

## 6. Image Replacement

-   [ ] Allow editing an existing wishlist item
-   [ ] Select a new image
-   [ ] Upload replacement image
-   [ ] Update `Gift.image_url`
-   [ ] Delete the old local image after successful replacement
-   [ ] Preserve external image URLs
-   [ ] Prevent accidental deletion of an external image

Flow:

``` text
Edit Item
    ↓
Choose New Image
    ↓
Upload New Image
    ↓
Save New Image URL
    ↓
Delete Old Local Image
```

------------------------------------------------------------------------

## 7. Remove Image

-   [ ] Add option to remove an image
-   [ ] Clear `Gift.image_url`
-   [ ] Delete the corresponding local image
-   [ ] Keep the wishlist item
-   [ ] Do not attempt to delete external images

Flow:

``` text
Remove Image
     ↓
Delete local file
     ↓
Set image_url = null
```

------------------------------------------------------------------------

## 8. Delete Item Cleanup

When a wishlist item is deleted:

-   [ ] Check whether its image is a local Wilik image
-   [ ] Delete the local image
-   [ ] Delete the Gift record
-   [ ] Prevent orphaned image files

Flow:

``` text
Delete Item
     ↓
Check image_url
     ↓
Local image?
   /      Yes      No
  ↓        ↓
Delete   Nothing
file
  ↓
Delete Gift
```

------------------------------------------------------------------------

## 9. Supported Formats

### Must work

-   [ ] JPG
-   [ ] JPEG
-   [ ] PNG
-   [ ] WebP
-   [ ] GIF

### Must reject

-   [ ] SVG
-   [ ] Executable files
-   [ ] Text files
-   [ ] Arbitrary renamed files
-   [ ] Unsupported formats

------------------------------------------------------------------------

## 10. Persistence Testing

-   [x] Upload image
-   [x] Verify image appears
-   [ ] Restart backend container
-   [ ] Verify image still appears
-   [ ] Restart frontend container
-   [ ] Verify image still appears
-   [ ] Restart entire Wilik stack
-   [ ] Verify image still appears
-   [ ] Verify image remains in external storage

------------------------------------------------------------------------

## 11. Backup & Restore

Images are stored separately from the application container.

Backup:

``` text
/mnt/Bigdata/wilik/images/
```

Test:

-   [ ] Back up image directory
-   [ ] Restore image directory
-   [ ] Restore Wilik database
-   [ ] Verify image URLs still work
-   [ ] Verify wishlist cards display restored images
-   [ ] Document restore procedure

------------------------------------------------------------------------

## 12. Security

-   [ ] Enforce upload size limit
-   [ ] Validate actual image content
-   [ ] Restrict file formats
-   [ ] Generate random filenames
-   [x] Do not use original filenames for storage
-   [ ] Prevent path traversal
-   [ ] Keep uploads outside application source
-   [ ] Ensure uploaded files cannot execute as application code

------------------------------------------------------------------------

## Definition of Done

This image milestone is complete when:

-   [ ] Images have a size limit
-   [ ] Images are validated as real images
-   [ ] Unsupported formats are rejected
-   [ ] Images are resized when necessary
-   [ ] Images are converted to optimized WebP
-   [ ] Images are stored on dedicated storage
-   [ ] Images load through `/api/uploads/...`
-   [ ] Images can be replaced
-   [ ] Images can be removed
-   [ ] Images are deleted when their wishlist item is deleted
-   [ ] No orphaned image files remain
-   [ ] Images survive container restarts
-   [ ] Image backup and restore has been tested

# 🖼️ Image Milestone Complete

**Wilik has a secure, optimized, persistent local image system ready for
production.**
