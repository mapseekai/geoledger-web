# Design and content system

The product is an engineering tool, not a consumer map showcase. The home page therefore starts with the version workflow and an honest product explanation, then moves to real console evidence, architecture and task-based documentation.

## Brand tokens

- Mark orange: #fa520f; accessible action/text orange: #cc3a05.
- Navigation: #0b1220; ink: #101828; secondary: #344054; muted: #667085.
- Page/surface: white and #f5f6f8; border: #e4e7ec; accent wash: #fff4ed.
- Dark surfaces and accent pairs are explicit; screenshots retain original pixels.

## Information architecture

Home explains the workflow and offers three entry points. Docs separates learning, how-to tasks, reference contracts and explanation. Blog labels Release and Main independently. The pinned implementation is the source of truth, not the pre-existing promotional article.

## Quality gates

No invented Git branches, real-time CRDT behavior, database migration guarantees or performance multipliers. Diagram boxes describe responsibilities, not mandatory microservices. Core merge logic is a dependency of Application, not a database proxy. All declared screenshots have provenance.

Native OINK search, navigation, TOC, keyboard support and appearance controls are retained. New layout components respect visible focus, semantic links, image dimensions, responsive stacking and reduced-motion preferences. Static content must remain readable without custom JavaScript.
