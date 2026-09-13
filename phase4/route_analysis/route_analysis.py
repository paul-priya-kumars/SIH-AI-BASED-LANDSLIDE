# ============================================
# PHASE 4.1 - ROUTE ANALYSIS
# ============================================

# Route information
routes = {
    "Route A": {
        "distance": 5,
        "risk": 30
    },
    "Route B": {
        "distance": 8,
        "risk": 85
    },
    "Route C": {
        "distance": 6,
        "risk": 55
    }
}


# ============================================
# FUNCTION: GET RISK LEVEL
# ============================================

def get_risk_level(risk):
    if risk < 40:
        return "LOW"
    elif risk < 70:
        return "MODERATE"
    else:
        return "HIGH"


# ============================================
# DISPLAY ROUTE ANALYSIS
# ============================================

print("\n============================================")
print("        PHASE 4.1 - ROUTE ANALYSIS")
print("============================================\n")

safe_routes = []
moderate_routes = []
risky_routes = []

for route, data in routes.items():

    distance = data["distance"]
    risk = data["risk"]

    level = get_risk_level(risk)

    if level == "LOW":
        safe_routes.append(route)

    elif level == "MODERATE":
        moderate_routes.append(route)

    else:
        risky_routes.append(route)

    print(
        f"{route}: "
        f"Distance = {distance} km | "
        f"Risk Score = {risk}/100 | "
        f"Risk Level = {level}"
    )


# ============================================
# DISPLAY ROUTE CATEGORIES
# ============================================

print("\n============================================")
print("              ROUTE CATEGORIES")
print("============================================")

print("\nSafe Routes:")
if safe_routes:
    for route in safe_routes:
        print(f"  - {route}")
else:
    print("  None")

print("\nModerate Risk Routes:")
if moderate_routes:
    for route in moderate_routes:
        print(f"  - {route}")
else:
    print("  None")

print("\nHigh Risk Routes:")
if risky_routes:
    for route in risky_routes:
        print(f"  - {route}")
else:
    print("  None")


# ============================================
# FIND SAFEST ROUTE
# ============================================

safest_route = min(
    routes,
    key=lambda route: routes[route]["risk"]
)

safest_risk = routes[safest_route]["risk"]
safest_distance = routes[safest_route]["distance"]
safest_level = get_risk_level(safest_risk)


# ============================================
# ROUTE RECOMMENDATION
# ============================================

print("\n============================================")
print("           ROUTE RECOMMENDATION")
print("============================================")

print(f"\nRecommended Route : {safest_route}")
print(f"Distance          : {safest_distance} km")
print(f"Risk Score        : {safest_risk}/100")
print(f"Risk Level        : {safest_level}")

if safest_risk < 40:
    print("Recommendation    : SAFE ROUTE")
    print("Status            : PROCEED")

elif safest_risk < 70:
    print("Recommendation    : USE WITH CAUTION")
    print("Status            : CAUTION")

else:
    print("Recommendation    : AVOID IF POSSIBLE")
    print("Status            : WARNING")


# ============================================
# END
# ============================================

print("\n============================================")
print("        ROUTE ANALYSIS COMPLETED")
print("============================================\n")