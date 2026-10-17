"""Read-only collected-data API. Saving/completing remains in the separate demo."""
from flask import Blueprint, jsonify, request

try:
    from .catalog_reader import load_catalog
except ImportError:
    from catalog_reader import load_catalog


def register_catalog(app):
    blueprint = Blueprint("catalog", __name__, url_prefix="/catalog")

    @blueprint.get("/options")
    def options():
        try:
            return jsonify(load_catalog().taxonomy)
        except FileNotFoundError:
            return jsonify(error="Catalog not exported. Run python -m opportunity_data.export_app"), 503

    @blueprint.get("/opportunities")
    def opportunities():
        args = request.args
        try:
            allowed = {"interests", "goals", "challenge_levels", "time_buckets", "locations", "commitment", "q", "scope", "lat", "lon", "radius_km", "include_past", "source", "kind", "offset", "limit", "skills", "experience", "cost", "prerequisites", "duration_quality", "schedule", "max_minutes", "match_mode"}
            if set(args) - allowed:
                raise ValueError("Unknown filter parameters: " + ", ".join(sorted(set(args) - allowed)))
            flag = args.get("include_past", "false")
            if flag not in {"true", "false"}:
                raise ValueError("include_past must be true or false")
            result = load_catalog().query(
                **{key: args.getlist(key) for key in ("interests", "goals", "challenge_levels", "time_buckets", "locations", "skills", "experience", "cost", "prerequisites", "duration_quality", "schedule")},
                max_minutes=float(args["max_minutes"]) if "max_minutes" in args else None,
                match_mode=args.get("match_mode", "any"), commitment=args.get("commitment"), q=args.get("q", ""), scope=args.get("scope", "opportunity"),
                lat=float(args["lat"]) if "lat" in args else None,
                lon=float(args["lon"]) if "lon" in args else None,
                radius_km=float(args.get("radius_km", "25")), include_past=flag == "true",
                source=args.get("source"), kind=args.get("kind"),
                offset=int(args.get("offset", "0")), limit=int(args.get("limit", "20")))
            return jsonify(result)
        except FileNotFoundError:
            return jsonify(error="Catalog not exported. Run python -m opportunity_data.export_app"), 503

    app.register_blueprint(blueprint)
