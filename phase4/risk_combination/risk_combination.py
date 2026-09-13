# ============================================
# PHASE 4.3 - RISK COMBINATION
# ============================================

print("\n============================================")
print("       PHASE 4.3 - RISK COMBINATION")
print("============================================\n")


# ============================================
# INPUT 1 - ML RISK
# ============================================

# TEST VALUE
# We will connect the actual Phase 3 ML result later.

ml_risk = "MEDIUM"


# ============================================
# INPUT 2 - ROUTE RISK
# ============================================

# TEST VALUE
# We will connect the actual route-risk result later.

route_risk = "LOW"


# ============================================
# INPUT 3 - CITIZEN IMAGE ANALYSIS
# ============================================

image_result = {
    "landslide": False,
    "flooding": True,
    "road_damage": False
}


# ============================================
# ANALYZE IMAGE RISK
# ============================================

image_risk = "LOW"

if image_result["landslide"]:
    image_risk = "HIGH"

elif image_result["flooding"]:
    image_risk = "HIGH"

elif image_result["road_damage"]:
    image_risk = "MEDIUM"


# ============================================
# DISPLAY INPUT RISKS
# ============================================

print("Risk Inputs:")
print("ML Risk    :", ml_risk)
print("Route Risk :", route_risk)
print("Image Risk :", image_risk)


# ============================================
# RISK LEVEL VALUES
# ============================================

risk_values = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
}


# ============================================
# COMBINE RISKS
# ============================================

overall_value = max(
    risk_values[ml_risk],
    risk_values[route_risk],
    risk_values[image_risk]
)


if overall_value == 3:
    overall_risk = "HIGH"

elif overall_value == 2:
    overall_risk = "MEDIUM"

else:
    overall_risk = "LOW"


# ============================================
# FINAL DECISION
# ============================================

print("\n============================================")
print("             FINAL RISK STATUS")
print("============================================")

print("Overall Risk:", overall_risk)


if overall_risk == "HIGH":
    print("ALERT: High disaster risk detected!")
    print("ACTION: Avoid the affected route.")

elif overall_risk == "MEDIUM":
    print("WARNING: Moderate disaster risk detected.")
    print("ACTION: Travel with caution.")

else:
    print("STATUS: Low disaster risk.")
    print("ACTION: Route appears relatively safe.")


# ============================================
# END
# ============================================

print("\n============================================")
print("       RISK COMBINATION COMPLETED")
print("============================================\n")