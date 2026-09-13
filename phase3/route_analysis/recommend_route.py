def get_recommendation(risk_score):
    """Return a recommendation based on route risk."""

    if risk_score < 40:
        return {
            "recommendation": "SAFE ROUTE",
            "status": "PROCEED",
        }

    elif risk_score < 70:
        return {
            "recommendation": "USE WITH CAUTION",
            "status": "CAUTION",
        }

    else:
        return {
            "recommendation": "AVOID IF POSSIBLE",
            "status": "WARNING",
        }


def main():
    print("\n============================================")
    print("   PHASE 3.9.2 - ROUTE RISK RECOMMENDATION")
    print("============================================\n")

    routes = {
        "Route A": {
            "distance": 5,
            "risk": 30,
        },
        "Route B": {
            "distance": 8,
            "risk": 85,
        },
        "Route C": {
            "distance": 6,
            "risk": 55,
        },
    }

    print("Route Recommendations:")

    for route, data in routes.items():

        result = get_recommendation(data["risk"])

        print(
            f"\n{route}"
        )

        print(
            f"  Distance       : "
            f"{data['distance']} km"
        )

        print(
            f"  Risk Score     : "
            f"{data['risk']}/100"
        )

        print(
            f"  Recommendation : "
            f"{result['recommendation']}"
        )

        print(
            f"  Status         : "
            f"{result['status']}"
        )

    print("\n============================================")
    print("      PHASE 3.9.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
