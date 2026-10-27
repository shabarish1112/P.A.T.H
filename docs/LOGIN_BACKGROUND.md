# Login background photo

The marked navigation cards, sidebar, theme control and sign-in panel use shared
adaptive glass tokens in frontend/src/index.css. Data cards, layout, navigation,
authentication and permissions are unchanged. Reduced transparency and forced-color
preferences use opaque surfaces; browsers without backdrop blur also get opaque
panels. Existing reduced-motion rules continue to apply.

To add a photo later:

1. Put an optimized image in frontend/public/images/login-background.webp. Create
   the images folder if needed. Use your own licensed image and a lowercase filename.
2. For local development, set VITE_LOGIN_BACKGROUND_IMAGE=/images/login-background.webp
   in frontend/.env.local and restart Vite.
3. For Vercel, add the same key/value to the project's environment variables and
   redeploy after committing the image. This value is public, not a secret.
4. Leave the value empty to use the supplied soft color backdrop.

Supported extensions: webp, avif, png, jpg and jpeg. Use a local root-relative path;
external URLs and unsafe paths are ignored to preserve the existing content-security
policy. Export photographs without personal/location metadata and preferably below
500 KB. Keep the focal point outside the centered panel; its tint and blur protect
form readability. No image is bundled until you supply one.
