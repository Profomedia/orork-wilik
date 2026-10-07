import { useState, useEffect } from 'react'
import StarRating from './StarRating'
import { CURRENCY_OPTIONS } from '../formOptions'

const API_BASE = '/api'

function GiftForm({ initialValues, defaultCurrency, onSubmit, onCancel }) {
  const [values, setValues] = useState({
    title: initialValues?.title ?? '',
    label: initialValues?.label ?? '',
    brand: initialValues?.brand ?? '',
    options: initialValues?.options ?? '',
    url: initialValues?.url ?? '',
    image_url: initialValues?.image_url ?? '',
    description: initialValues?.description ?? '',
    price: initialValues?.price ?? '',
    currency: initialValues?.currency ?? '__default__',
    quantity: initialValues?.quantity ?? 1,
  })

  const [unlimited, setUnlimited] = useState(
    initialValues ? initialValues.quantity == null : false
  )

  const [rating, setRating] = useState(
    initialValues?.rating ?? null
  )

  const [scraping, setScraping] = useState(false)
  const [scrapeError, setScrapeError] = useState(null)
  const [imagePreviewError, setImagePreviewError] = useState(false)

  // New image upload state
  const [imageFile, setImageFile] = useState(null)
  const [imageFilePreview, setImageFilePreview] = useState(null)
  const [removeImage, setRemoveImage] = useState(false)

  useEffect(() => {
    setImagePreviewError(false)
  }, [values.image_url])

  // Clean up temporary browser preview URL
  useEffect(() => {
    return () => {
      if (imageFilePreview) {
        URL.revokeObjectURL(imageFilePreview)
      }
    }
  }, [imageFilePreview])

  function handleChange(event) {
    const { name, value } = event.target

    setValues((current) => ({
      ...current,
      [name]: value,
    }))
  }

  function handleImageChange(event) {
  const file = event.target.files?.[0]

  if (!file) {
    setImageFile(null)
    setImageFilePreview(null)
    return
  }

  setImageFile(file)
  setImageFilePreview(URL.createObjectURL(file))
  setRemoveImage(false)

  // Clear external image URL when selecting a local image.
  setValues((current) => ({
    ...current,
    image_url: '',
  }))

  setImagePreviewError(false)
}

  function handleFetchDetails() {
    setScraping(true)
    setScrapeError(null)

    fetch(`${API_BASE}/scrape`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: values.url,
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,
          data,
        }))
      )
      .then(({ ok, data }) => {
        if (!ok) {
          setScrapeError(
            data.error ||
              'Could not fetch details for that URL'
          )
          return
        }

        setValues((current) => ({
          ...current,
          title: data.title || current.title,
          image_url:
            data.image_url || current.image_url,
          brand: data.brand || current.brand,
          price:
            data.price != null
              ? data.price
              : current.price,
        }))

        // If scraper provides an image URL, remove any
        // locally selected image because the fetched image
        // is now the current image choice.
        setImageFile(null)
        setImageFilePreview(null)
      })
      .catch(() =>
        setScrapeError(
          'Could not fetch details for that URL'
        )
      )
      .finally(() => setScraping(false))
  }

  function handleSubmit(event) {
    event.preventDefault()

    const formData = new FormData()

    formData.append('title', values.title)

    if (values.label) {
      formData.append('label', values.label)
    }

    // Image handling
    if (removeImage) {
      formData.append('remove_image', 'true')
    } else if (imageFile) {
      formData.append('image', imageFile)
    } else if (values.image_url) {
      formData.append('image_url', values.image_url)
    }

    if (values.brand) {
      formData.append('brand', values.brand)
    }

    if (values.options) {
      formData.append('options', values.options)
    }

    if (values.url) {
      formData.append('url', values.url)
    }

    if (values.description) {
      formData.append(
        'description',
        values.description
      )
    }

    if (values.price !== '') {
      formData.append(
        'price',
        values.price
      )
    }

    if (values.currency !== '__default__') {
      formData.append(
        'currency',
        values.currency
      )
    }

    formData.append(
      'quantity',
      unlimited
        ? ''
        : String(Number(values.quantity) || 1)
    )

    if (rating != null) {
      formData.append(
        'rating',
        rating
      )
    }


    onSubmit(formData)
  }

  return (
    <form
      className="gift-form"
      onSubmit={handleSubmit}
    >
      {/* URL */}
      <label>
        URL

        <span className="inline-field">
          <input
            name="url"
            value={values.url}
            onChange={handleChange}
            placeholder="https://..."
          />

          <button
            type="button"
            className="btn-primary"
            onClick={handleFetchDetails}
            disabled={!values.url || scraping}
          >
            {scraping
              ? 'Fetching…'
              : 'Fetch details'}
          </button>
        </span>
      </label>

      {scrapeError && (
        <p className="form-error">
          {scrapeError}
        </p>
      )}

      {/* Image upload */}
      <label>
        Image

        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={handleImageChange}
        />
      </label>

      {/* Uploaded image preview */}
      {imageFilePreview && (
        <img
          src={imageFilePreview}
          alt="Selected image preview"
          className="gift-form__image-preview"
        />
      )}

      {/* Existing/external image URL */}
      {!imageFile && (
        <>
          <label>
            Image URL

            <input
              name="image_url"
              value={values.image_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </label>

          {values.image_url &&
            !imagePreviewError && (
              <img
                src={values.image_url}
                alt="Preview"
                className="gift-form__image-preview"
                onError={() =>
                  setImagePreviewError(true)
                }
              />
            )}
        </>
      )}

      {/* Label + Brand */}
      {(imageFilePreview || values.image_url) && (
        <button
          type="button"
          onClick={() => {
            setImageFile(null)
            setImageFilePreview(null)
            setRemoveImage(false)

            setValues((current) => ({
              ...current,
              image_url: '',
            }))

            setImagePreviewError(false)
          }}
        >
          Remove image
        </button>
      )}

      {/* Title */}
      <label>
        <span>
          Title{' '}
          <span className="required">
            *
          </span>
        </span>

        <input
          name="title"
          value={values.title}
          onChange={handleChange}
          placeholder="e.g. Rummikub, Bleu de Chanel, Animal Farm ..."
          required
        />
      </label>

      {/* Options */}
      <label>
        Product options (separate with semicolons)

        <input
          name="options"
          value={values.options}
          onChange={handleChange}
          placeholder="e.g. Medium; 50ml; Black, blue or yellow"
        />
      </label>

      {/* Description */}
      <label>
        Description

        <textarea
          name="description"
          value={values.description}
          onChange={handleChange}
          placeholder="Any extra details worth mentioning"
        />
      </label>

      {/* Price + Currency + Quantity */}
      <div className="gift-form__row">
        <label>
          Price

          <input
            name="price"
            type="number"
            step="any"
            value={values.price}
            onChange={handleChange}
            placeholder="0,00"
          />
        </label>

        <label>
          Currency

          <select
            name="currency"
            value={values.currency}
            onChange={handleChange}
          >
            <option value="__default__">
              Default (
              {defaultCurrency ||
                'no symbol'}
              )
            </option>

            {CURRENCY_OPTIONS.map(
              (option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              )
            )}
          </select>
        </label>

        <label>
          Quantity

          <input
            name="quantity"
            type="number"
            min="1"
            value={
              unlimited
                ? ''
                : values.quantity
            }
            onChange={handleChange}
            disabled={unlimited}
          />
        </label>
      </div>

      {/* Unlimited */}
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={unlimited}
          onChange={(event) =>
            setUnlimited(
              event.target.checked
            )
          }
        />

        Unlimited (anyone can claim a copy,
        it never runs out)
      </label>

      {/* Rating */}
      <label>
        Rating

        <StarRating
          value={rating}
          onChange={setRating}
        />
      </label>

      {/* Actions */}
      <div className="gift-form__actions">
        <button type="submit">
          Save
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}

export default GiftForm