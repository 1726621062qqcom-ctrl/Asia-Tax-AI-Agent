<a id="asiatax-标志落地"></a>

# AsiaTax Brand Implementation

On 2026-09-28, the user approved the T-shaped logo from the concept image. This round covers original vector assets and existing frontend branding entry points; sign-in/registration and a full interface redesign are separate work.

The mark consists of a wide top bar, central vertical stroke, and short side bars, emphasizing Tax without an A or scales. The primary color is dark green `#173F35`, the reversed color is warm white `#F7F6F0`, and the accent is `#A7BAAA`. The wordmark uses regular weight for Asia and bold for Tax.

The sidebar and startup page use a reusable Brand component; the welcome page uses a standalone symbol. The favicon is a reversed mark on dark green. Standalone SVGs provide dark/reversed versions, with a PNG mobile bookmark icon. The mark makes no promise of fixed tax savings.

Components with wordmarks use one accessible AsiaTax name, hiding internal graphics from screen readers; decorative graphics add no spoken content. Resizing preserves geometric proportions. Add no animation or dependencies.

Follow existing Lucide SVG integration conventions. The artwork is original and copies no third-party marks. Validate the production build and existing browser tests, and inspect actual pages and the mark at small sizes.
