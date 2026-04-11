# Atlas

This is a feature-primary Next.js app. Each ontology form owns a folder under `college-atlas/`; the State Atlas owns `state-atlas/`; cross-cutting infrastructure lives in `scene/`, `ui/`, `auth/`, and `config/`.

Before adding, moving, or reorganizing files under `atlas/`, read [`atlas/docs/the-structure.md`](./docs/the-structure.md). It defines the folder contract, the intended cross-feature dependency, the one known tension (`partnerships/savedProposals.ts`), and the anti-patterns the layout exists to prevent.

For product context on what the atlas is and what each form represents, start with [`docs/product/the-atlas.md`](../docs/product/the-atlas.md) and the per-form documents under `docs/product/`.
