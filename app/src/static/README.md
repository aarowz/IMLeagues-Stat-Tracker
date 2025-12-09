# Static Directory

This directory contains static assets for the Streamlit application, including images, icons, and other media files.

## Contents

- `logo.png` - Application logo used in the sidebar navigation

## Usage

Static files are configured in `app/src/.streamlit/config.toml` with the `staticDirs` setting. Reference static files in your Streamlit code using:

```python
st.image("static/logo.png")
# or
st.sidebar.image("static/logo.png", width=150)
```

## Adding New Static Files

1. Place the file in this `static/` directory
2. Reference it in your Streamlit code using the path `static/filename`
3. Streamlit will automatically serve it

## Best Practices

- Keep file sizes reasonable to minimize load times
- Use appropriate file formats (PNG for images with transparency, JPG for photos)
- Organize files into subdirectories if you have many assets (e.g., `static/images/`, `static/icons/`)

## Reference

For more information on serving static files in Streamlit, see:
https://docs.streamlit.io/develop/concepts/configuration/serving-static-files
