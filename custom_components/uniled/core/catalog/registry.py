"""Model catalog registry."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from functools import cache
from importlib import resources

from .schema import CatalogModel, SupportLevel


class ModelCatalog:
    """Searchable registry of all known catalog model records."""

    def __init__(self, models: Iterable[CatalogModel]) -> None:
        self._models = tuple(sorted(models, key=lambda model: model.model_id))
        self._by_model_id = {model.model_id: model for model in self._models}

        by_name: dict[str, list[CatalogModel]] = defaultdict(list)
        by_label: dict[str, list[CatalogModel]] = defaultdict(list)
        for model in self._models:
            by_name[model.name.casefold()].append(model)
            labels = {model.name.strip(), model.friendly_name.strip()}
            for label in labels:
                if label:
                    by_label[label.casefold()].append(model)
        self._by_name = {
            name: tuple(sorted(models, key=_canonical_sort_key))
            for name, models in by_name.items()
        }
        self._by_label = {
            label: tuple(sorted(models, key=_canonical_sort_key))
            for label, models in by_label.items()
        }

    @property
    def models(self) -> tuple[CatalogModel, ...]:
        """All catalog records."""
        return self._models

    @property
    def model_ids(self) -> frozenset[int]:
        """All catalog model IDs."""
        return frozenset(self._by_model_id)

    @property
    def unique_names(self) -> frozenset[str]:
        """All unique catalog names."""
        return frozenset(model.name for model in self._models)

    @property
    def user_facing_names(self) -> frozenset[str]:
        """All names that should be represented to users."""
        return frozenset(model.name for model in self.user_facing_models())

    @property
    def user_facing_labels(self) -> frozenset[str]:
        """All names and friendly labels that can identify user-facing models."""
        labels: set[str] = set()
        for model in self.user_facing_models():
            labels.add(model.name)
            if model.friendly_name:
                labels.add(model.friendly_name)
        return frozenset(labels)

    def get_model_id(self, model_id: int) -> CatalogModel:
        """Return a model by numeric catalog ID."""
        return self._by_model_id[model_id]

    def models_for_name(self, name: str) -> tuple[CatalogModel, ...]:
        """Return all catalog variants for a model name."""
        return self._by_name.get(name.casefold(), ())

    def models_for_label(self, label: str) -> tuple[CatalogModel, ...]:
        """Return all catalog variants matching a name or friendly label."""
        return self._by_label.get(label.casefold(), ())

    def resolve_name(self, name: str) -> CatalogModel | None:
        """Return the canonical catalog record for a name."""
        matches = self.models_for_name(name)
        return matches[0] if matches else None

    def resolve_label(self, label: str) -> CatalogModel | None:
        """Return the canonical catalog record for a name or friendly label."""
        matches = self.models_for_label(label)
        return matches[0] if matches else None

    def resolve_model(
        self,
        name: str,
        *,
        model_id: int | None = None,
    ) -> CatalogModel | None:
        """Return the catalog record matching a name and optional APK model ID."""
        if model_id is None:
            return self.resolve_name(name)
        for model in self.models_for_name(name):
            if model.model_id == model_id:
                return model
        return None

    def resolve_model_label(
        self,
        label: str,
        *,
        model_id: int | None = None,
    ) -> CatalogModel | None:
        """Return the model matching a name/friendly label and optional APK ID."""
        if model_id is None:
            return self.resolve_label(label)
        for model in self.models_for_label(label):
            if model.model_id == model_id:
                return model
        return None

    def user_facing_models(self) -> tuple[CatalogModel, ...]:
        """Return canonical user-facing model records."""
        return tuple(
            model
            for name in sorted(self.unique_names)
            if (model := self.resolve_name(name)) is not None
            and model.support_level is not SupportLevel.FILTERED
        )

    def filtered_models(self) -> tuple[CatalogModel, ...]:
        """Return records that are intentionally hidden from users."""
        return tuple(
            model
            for model in self._models
            if model.support_level is SupportLevel.FILTERED
        )


def _canonical_sort_key(model: CatalogModel) -> tuple[int, int, int]:
    filtered = int(model.support_level is SupportLevel.FILTERED)
    child = int(model.parent_id is not None)
    return (filtered, child, model.model_id)


@cache
def default_catalog() -> ModelCatalog:
    """Load the bundled model catalog."""
    source = resources.files(__package__).joinpath("models.json")
    raw_models = json.loads(source.read_text(encoding="utf-8"))
    return ModelCatalog(CatalogModel.from_dict(raw) for raw in raw_models)
