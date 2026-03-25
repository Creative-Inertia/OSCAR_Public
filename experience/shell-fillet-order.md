---
name: Apply fillets before shell, not after
type: lesson
tags: [shell, fillet, feature-order, box]
---

**What:** Fillets on outer vertical edges must be applied BEFORE the shell feature, not after.

**Details:** When building a hollow box (extrude + shell), the shell operation transforms the body topology so that the original outer corner edges no longer exist as simple vertical line segments. After shell, the only vertical edges are the inner wall corners, and the outer corners become compound edges that are hard to select programmatically.

The correct feature order is:
1. Extrude solid block
2. Fillet the outer vertical corner edges
3. Shell (remove top face, set wall thickness)

**Why it matters:** If you shell first then try to fillet, you can't find the outer corner edges — they've been absorbed into the shell topology. You'll waste multiple API calls debugging "0 corner edges found" before realizing the feature order is wrong.
