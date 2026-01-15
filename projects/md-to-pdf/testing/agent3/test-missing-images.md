# Test: Missing Images

This document tests how the converter handles references to non-existent image files.

## Scenario 1: Missing Local Image

Here's a reference to an image that doesn't exist:

![Missing Image](./does-not-exist.png)

The converter should handle this gracefully without crashing.

## Scenario 2: Missing Remote Image

Here's a reference to a remote image that doesn't exist:

![Missing Remote Image](https://example.com/nonexistent-image-12345.jpg)

## Scenario 3: Multiple Missing Images

![First Missing](./missing1.png)

Some text between images.

![Second Missing](./missing2.jpg)

More text.

![Third Missing](./missing3.gif)

## Expected Behavior

The converter should:
- Display a warning or placeholder for missing images
- Continue processing the rest of the document
- Not crash or fail completely
