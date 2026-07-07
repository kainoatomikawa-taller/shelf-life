"""SQLAlchemy ORM models.

ORM types are confined to the infrastructure layer and never leak into
domain or application.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base

# Named enum types — defined once so SQLAlchemy does not attempt duplicate DDL.
_ingredient_category = Enum(
    "perishable_fridge",
    "perishable_counter",
    "frozen",
    "pantry",
    "spice",
    name="ingredient_category",
)

_storage_location = Enum(
    "fridge",
    "counter",
    "freezer",
    "pantry",
    name="storage_location",
)

_shelf_life_model_type = Enum(
    "spoilage",
    "potency",
    name="shelf_life_model_type",
)

_substitution_context_type = Enum(
    "baking",
    "savory",
    "general",
    name="substitution_context",
)

_diet_type = Enum(
    "omnivore",
    "vegetarian",
    "vegan",
    "pescatarian",
    "keto",
    "paleo",
    "gluten_free",
    "dairy_free",
    "halal",
    "kosher",
    name="diet_type",
)

_skill_level = Enum(
    "beginner",
    "intermediate",
    "advanced",
    name="skill_level",
)

_license = Enum(
    "public-domain",
    "cc0",
    "cc-by",
    "cc-by-sa",
    "self-authored",
    name="recipe_license",
)

_budget_sensitivity = Enum(
    "low",
    "medium",
    "high",
    name="budget_sensitivity",
)

_quantity_state = Enum(
    "in",
    "low",
    "out",
    name="quantity_state",
)

_freshness_date_type = Enum(
    "package",
    "est-from-purchase",
    "est-unknown",
    name="freshness_date_type",
)

_freshness_display_status = Enum(
    "fresh",
    "use_soon",
    "use_now",
    "past_estimate_check_it",
    name="freshness_display_status",
)

_ingredient_role = Enum(
    "essential",
    "optional",
    name="ingredient_role",
)

_pipeline_stage = Enum(
    "imported",
    "tagged",
    "approved",
    "rejected",
    "published",
    name="pipeline_stage",
)


class PantryItemModel(Base):
    """Persistence representation of a pantry item."""

    __tablename__ = "pantry_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)


class IngredientModel(Base):
    """Persistence representation of a catalog ingredient (§8 schema)."""

    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Queryable via GIN index; use `'alias' = ANY(aliases)` in queries.
    aliases: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    category: Mapped[str] = mapped_column(_ingredient_category, nullable=False)
    default_storage_location: Mapped[str] = mapped_column(
        _storage_location, nullable=False
    )

    # typicalShelfLifeByStorage — per-location values in days, None = not applicable.
    shelf_life_fridge_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_counter_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_freezer_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_pantry_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    allergen_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    diet_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    # Distinguishes safety-based expiry (spoilage) from quality-loss (potency).
    # All spices use potency; everything else defaults to spoilage.
    shelf_life_model: Mapped[str] = mapped_column(
        _shelf_life_model_type,
        nullable=False,
        server_default="spoilage",
    )

    __table_args__ = (
        # GIN index enables efficient `'alias' = ANY(aliases)` lookups (AC-4).
        Index("ix_ingredients_aliases_gin", "aliases", postgresql_using="gin"),
    )


class SubstitutionModel(Base):
    """Persistence representation of an ingredient substitution (§8/§5.5 schema)."""

    __tablename__ = "substitutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Directed: "use to_ingredient instead of from_ingredient".
    from_ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Free-text ratio guidance, e.g. "use ¾ the amount".
    ratio_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    context: Mapped[str] = mapped_column(_substitution_context_type, nullable=False)

    # Free-text description of the culinary impact of the swap.
    impact_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # NUMERIC(4,3) stores exact decimals 0.000–1.000; supports reliable >= comparisons.
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(precision=4, scale=3), nullable=False
    )

    __table_args__ = (
        # Each ingredient pair may have at most one substitution per cooking context.
        UniqueConstraint(
            "from_ingredient_id",
            "to_ingredient_id",
            "context",
            name="uq_substitutions_pair_context",
        ),
        CheckConstraint(
            "from_ingredient_id != to_ingredient_id",
            name="ck_substitutions_no_self_reference",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_substitutions_confidence_range",
        ),
        # B-tree index supports threshold queries: WHERE confidence >= :threshold
        Index("ix_substitutions_confidence", "confidence"),
    )


class UserModel(Base):
    """Persistence representation of a user's taste profile (§8/§4.6 schema).

    Columns are grouped to mirror the domain split between hard constraints
    (allergies, diet_type — safety-critical, never relaxed) and soft
    preferences (everything else — used for ranking only). flavor_profile_*
    and taste_vector_* flatten their respective value objects into scalar
    columns, one per FLAVOR_DIMENSIONS entry, following the same pattern used
    for typicalShelfLifeByStorage on ingredients.

    `id` is `auth.users.id` — same convention as `ProfileModel` — so RLS
    policies on this table can scope rows via `id = auth.uid()`.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)

    # --- Hard constraints (§4.6) — never relaxed for a recommendation. -----
    allergies: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    diet_type: Mapped[str] = mapped_column(
        _diet_type, nullable=False, server_default="omnivore"
    )

    # --- Soft preferences (§4.6) — affect ranking only. --------------------
    disliked_ingredients: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    liked_cuisines: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    flavor_profile_sweetness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_saltiness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_sourness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_bitterness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_spiciness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_umami: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )

    skill_level: Mapped[str] = mapped_column(
        _skill_level, nullable=False, server_default="beginner"
    )
    typical_time_available_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="30"
    )
    equipment: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    budget_sensitivity: Mapped[str] = mapped_column(
        _budget_sensitivity, nullable=False, server_default="medium"
    )
    adventurousness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )

    # --- Derived (§4.6) — seeded from flavor_profile, updated by ratings. --
    taste_vector: Mapped[list[float]] = mapped_column(
        ARRAY(Float),
        nullable=False,
        server_default=text("ARRAY[0.5,0.5,0.5,0.5,0.5,0.5]::float8[]"),
    )

    __table_args__ = (
        ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        CheckConstraint(
            "adventurousness >= 0 AND adventurousness <= 1",
            name="ck_users_adventurousness_range",
        ),
        CheckConstraint(
            "typical_time_available_minutes > 0",
            name="ck_users_typical_time_available_positive",
        ),
    )


class ProfileModel(Base):
    """Persistence representation of a user's public profile.

    `id` is the same id as `auth.users.id` — a profile extends the Supabase
    Auth identity rather than having one of its own — hence the FK/PK
    doubling as this table's only identity column. `auth.users` is managed
    by Supabase and isn't part of our ORM metadata, so it's referenced by
    schema-qualified name rather than a mapped model.

    `username` is stored pre-normalized (stripped + lowercased, enforced by
    the Profile entity's constructor) so a plain unique constraint gives
    case-insensitive uniqueness; the check constraint below defends that
    invariant against writes that bypass the application layer.

    `email` exists solely so the forgot-password edge function can resolve a
    username to an email server-side (Supabase Auth's own `auth.users` table
    isn't part of our migrations). It's nullable because profiles created
    before that column existed have none on file; every new profile supplies
    one.
    """

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        CheckConstraint(
            "username = lower(username)", name="ck_profiles_username_lowercase"
        ),
    )


class InventoryItemModel(Base):
    """Persistence representation of a user's inventory item (§8 schema).

    quantity_state is a coarse in/low/out signal rather than a precise
    amount. computed_freshness_date, freshness_date_type and freshness_status
    are derived by the freshness engine (FreshnessCalculator +
    FreshnessStatusResolver) and stored rather than recomputed on read.
    """

    __tablename__ = "inventory_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity_state: Mapped[str] = mapped_column(_quantity_state, nullable=False)
    storage_location: Mapped[str] = mapped_column(_storage_location, nullable=False)

    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    printed_package_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_frozen: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # --- Derived — populated by the freshness engine, not set directly. ----
    computed_freshness_date: Mapped[date] = mapped_column(Date, nullable=False)
    freshness_date_type: Mapped[str] = mapped_column(
        _freshness_date_type, nullable=False
    )
    freshness_status: Mapped[str] = mapped_column(
        _freshness_display_status, nullable=False
    )

    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class RecipeModel(Base):
    """Persistence representation of a catalog recipe (§8 schema).

    allergen_tags/diet_tags are intentionally absent — they're derived from
    the recipe's ingredients (via RecipeIngredientModel) at read time rather
    than stored, so they can never drift out of sync with the catalog.
    """

    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    cuisine_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    flavor_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    technique_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    equipment_needed: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    steps: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(_skill_level, nullable=False)
    popularity_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )

    # --- Licensing & attribution guardrails — every published recipe must
    # carry proof of where it came from and under what terms (§ Licensing &
    # attribution guardrails AC1). image_* is nullable: most recipes have no
    # image yet, but one is only ever storable under its own valid license
    # (AC3) — see RecipeImage.
    license: Mapped[str] = mapped_column(_license, nullable=False)
    source_attribution: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_license: Mapped[str | None] = mapped_column(_license, nullable=True)
    image_attribution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # flavor_profile_* — flattened FlavorProfile dimensions, same convention
    # as UserModel's, so a recipe's taste match can be scored by similarity
    # against a user's taste vector (§10 Step 3) rather than tag overlap.
    flavor_profile_sweetness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_saltiness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_sourness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_bitterness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_spiciness: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )
    flavor_profile_umami: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )

    __table_args__ = (
        CheckConstraint("time_minutes > 0", name="ck_recipes_time_minutes_positive"),
        CheckConstraint(
            "popularity_score >= 0", name="ck_recipes_popularity_score_non_negative"
        ),
    )


class RecipeIngredientModel(Base):
    """Persistence representation of a recipe's ingredient list (§8 schema).

    One row per (recipe, ingredient) pair, tagged essential or optional —
    the flag AC1 requires and the input to allergen/diet tag derivation.
    """

    __tablename__ = "recipe_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(_ingredient_role, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "recipe_id", "ingredient_id", name="uq_recipe_ingredients_pair"
        ),
    )


class ShoppingListItemModel(Base):
    """Persistence representation of a user's shopping list item (§8 schema).

    Populated by AddShoppingListItemsUseCase's one-tap add (§5.4) — one row
    per true-gap ingredient the user committed to buy. source_recipe_ids is
    provenance only; it doesn't gate anything at read time. quantity_needed
    is flattened into amount/unit columns, following the same convention as
    PantryItem's Quantity value object.
    """

    __tablename__ = "shopping_list_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_recipe_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    quantity_needed_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity_needed_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)


class RatingModel(Base):
    """Persistence representation of a user's recipe rating (§8 schema).

    Recorded once per cook, never edited in place — stars and quick_tags
    capture that single moment's feedback.
    """

    __tablename__ = "ratings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    quick_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    made_it_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )


class RawRecipeModel(Base):
    """Persistence representation of a staged raw recipe (recipe ingestion
    pipeline).

    Lives in its own table, entirely separate from RecipeModel — the whole
    point of staging is that untrusted, freeform source data never shares a
    table (or a schema) with the reviewed production catalog. published_recipe_id
    is a nullable FK set only once the pipeline reaches the published stage;
    ON DELETE SET NULL so deleting the published Recipe doesn't cascade into
    losing the staging/provenance record.
    """

    __tablename__ = "raw_recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_recipe_id: Mapped[str] = mapped_column(String(255), nullable=False)
    license: Mapped[str] = mapped_column(String(128), nullable=False)

    raw_name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_ingredients: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    raw_method: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    raw_attribution: Mapped[str | None] = mapped_column(Text, nullable=True)

    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    stage: Mapped[str] = mapped_column(
        _pipeline_stage, nullable=False, server_default="imported", index=True
    )

    # --- Tagging output (populated by TagRawRecipeUseCase /
    # TagStagedRecipesWithLlmUseCase) — null until the recipe reaches the
    # tagged stage. ---
    cuisine_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    flavor_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    technique_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    difficulty: Mapped[str | None] = mapped_column(_skill_level, nullable=True)
    time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_recipe_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "source", "source_recipe_id", name="uq_raw_recipes_source_pair"
        ),
    )


class RawRecipeIngredientModel(Base):
    """Persistence representation of one tagged ingredient line on a staged
    raw recipe (recipe ingestion pipeline).

    One row per raw ingredient line, mirroring RecipeIngredientModel's
    (recipe, ingredient, role) shape but with two differences that reflect
    staging data's untrusted, not-yet-fully-resolved nature: raw_text
    preserves the original freeform source line for a human reviewer to
    compare against, and ingredient_id is nullable — a raw recipe can reach
    the tagged stage with some ingredients still unmatched to the catalog,
    to be resolved during human review rather than blocking the batch.
    """

    __tablename__ = "raw_recipe_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    raw_recipe_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("raw_recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    ingredient_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(_ingredient_role, nullable=False)
