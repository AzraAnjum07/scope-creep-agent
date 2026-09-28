"""
Synthetic but realistic demo data: a freelance web project with a clear
original scope, followed by a client message a few weeks later that quietly
asks for work outside that scope.

Swap this out for real client threads later — the agent logic doesn't care
where the text comes from.
"""

PROJECT_ID = "brightleaf-website-redesign"

ORIGINAL_SCOPE = """
Project: Brightleaf Coffee Co. — Website Redesign
Client: Brightleaf Coffee Co. (contact: Priya Menon, Marketing Lead)
Agreed: 2026-08-03
Quote: ₹85,000, fixed price, 4-week timeline

Deliverables (in scope):
- Redesign of homepage, About, Menu, and Contact pages (4 pages total)
- Mobile-responsive layout
- New brand color palette applied across the site
- Basic on-page SEO (titles, meta descriptions) for the 4 pages
- One round of revisions after first draft

Explicitly out of scope (confirmed with client over call):
- No e-commerce / online ordering functionality
- No blog or CMS setup
- No custom illustrations (stock/licensed imagery only)
- No ongoing maintenance after handoff

Payment terms: 50% upfront, 50% on delivery.
"""

# A later message from the client that sounds like a small ask but is
# actually outside the agreed scope (online ordering = e-commerce, explicitly
# excluded above).
NEW_CLIENT_MESSAGE = """
Hey! Loving the new homepage design so far 🎉 Quick one — since you're
already in there, could you also add an "Order Online" button on the menu
page that lets customers actually place a pickup order and pay? Shouldn't
be too big a lift since the design's already done, right?
"""
