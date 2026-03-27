"""Application layer — composition root.

Assembles bounded contexts into runnable delivery mechanisms (``fastapi``,
``streamlit``). Owns no domain logic.

The app layer imports from bounded contexts. Bounded contexts never import from
this package. Adding or removing a delivery mechanism here has no impact on the
domains.
"""
