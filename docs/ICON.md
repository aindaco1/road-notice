# App icon

## In-app branding

Version 1.0.3 (11) uses the website's side-by-side icon and two-line wordmark in
the Settings header. `BrandHeader` scales with Dynamic Type and stacks the icon
above the wordmark when the horizontal layout no longer fits. VoiceOver reads
the brand once as a heading.

`BrandIcon.imageset/BrandIcon.png` is a relative symbolic link to the canonical
`AppIcon.appiconset/AppIcon.png`, so the app header, Home Screen icon and website
share one source image. Asset compilation follows that link; no image is fetched
at runtime. The header uses the website's 22% corner radius and tight monospaced
letter spacing.

## Original icon

Build 3 replaces the ticket with a simple roadside speed camera and a pale-blue prohibition overlay. The existing deep-blue, white and pale-blue palette is preserved.

The canonical asset is `App/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png`: a 1024 × 1024 opaque PNG. iOS supplies the rounded tile mask. The previous ticket-drawing script was removed so it cannot regenerate an obsolete icon.

The redesign was created with the built-in image-generation tool, using the prior icon as the palette reference, then resized for Apple's asset catalog. Prompt:

> Edit this app icon for Fine Me Not. Replace the outlined ticket with a very simple instantly recognizable roadside SPEED CAMERA pictogram: a white upright rectangular camera housing on a short white post, with one large deep-blue circular lens near the top and one small deep-blue rectangular flash below. Overlay a bold pale-light-blue prohibition symbol, a clean circular ring with a diagonal slash descending from upper left to lower right. Keep the camera lens legible beside the slash. Match the input's existing EXACT flat deep royal-blue background, white camera, and pale-light-blue overlay color. Extremely simple flat geometric icon, crisp smooth edges, centered, balanced, generous safe margin, readable at 48 pixels. No words, no letters, no speed numerals, no shadows, no gradients, no 3D, no texture, no border around the square, no rounded app tile corner rendering. Entire square canvas fully opaque with solid blue edge-to-edge. Deliver one 1024 by 1024 PNG production app-icon image.

Verified in the iPhone 16 Pro Max simulator Home Screen at normal icon size. The release archive passed the app bundle check with the updated icon.
