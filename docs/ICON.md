# App icon

## Camera-awareness revision — September 22, 2026

Released on the App Store with Road Notice 1.0.4 on September 25, 2026.

The current canonical icon replaces the prohibition symbol with a white road
and a pale-blue roadside marker on the existing blue background. It makes no
hardware-detection or enforcement-avoidance claim. The owner selected Road Notice
after the RoadCue naming check found an existing camera-alert product. The app
display name, two-line ROAD / NOTICE wordmark and website now use that choice.

The built-in image-generation tool produced the new artwork. Its 1254 x 1254
opaque PNG was mechanically resized with `sips` to the required 1024 x 1024 PNG.
`AppIcon.appiconset/AppIcon.png` remains the single canonical image. The existing
`BrandIcon` symbolic link and website staging script consume it unchanged.

Generation prompt:

> Create one production iOS app icon as a 1024 by 1024 fully opaque PNG. This is a neutral camera-awareness utility for driving. Use a flat solid deep royal-blue background exactly #0A0094 edge-to-edge. The symbol is a minimal white road in perspective rising gently from the lower-middle toward the upper-left, with a small pale-blue roadside marker at the upper-right of the road. Use only white #FFFFFF and pale blue #AECFFF on the blue background. The road should read as a single broad simple road silhouette with a few blue center-line cuts, not a navigation arrow, not a motorway interchange, not a letter. The marker is one simple solid circular pale-blue sign on a short pale-blue post, positioned alongside the upper section of the road, clearly separate from the road. Balanced compact composition with generous 16 percent safe margins, instantly legible at small app-icon sizes, crisp smooth geometric edges. Flat vector-like design, no words, no letters, no numbers, no camera or lens, no prohibition circle or slash, no radar arcs, no shield, no checkmark, no gradients, shadows, bevels, texture, border, or rendered rounded tile corners. Fill the entire square canvas with solid blue. Deliver only the single finished icon.

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
