/**
 * Realistic Mock Data for HomeRepair AI Consumer Frontend
 */

export const MOCK_APPLIANCES = [
  {
    id: 1,
    name: "Kitchen Refrigerator",
    brand: "Samsung",
    model_number: "RF28R7351SR",
    category: "refrigerator",
    purchase_date: "2023-10-15",
    warranty_expiry: "2025-10-15", // Expiring soon
    location: "Kitchen - Main Floor",
    notes: "French door 28 cu. ft. with Twin Cooling Plus & Food ShowCase door.",
    is_active: true,
    open_issue_count: 1,
    last_service_date: "2024-04-12",
  },
  {
    id: 2,
    name: "Laundry Washer",
    brand: "Whirlpool",
    model_number: "WFW5620HW",
    category: "washing_machine",
    purchase_date: "2021-06-20",
    warranty_expiry: "2022-06-20", // Expired
    location: "Basement Laundry",
    notes: "Front-load washer with Load & Go dispenser and Steam Clean option.",
    is_active: true,
    open_issue_count: 1,
    last_service_date: "2023-08-19",
  },
  {
    id: 3,
    name: "Dishwasher",
    brand: "Bosch",
    model_number: "SHP78CM5N",
    category: "dishwasher",
    purchase_date: "2024-01-10",
    warranty_expiry: "2026-01-10", // Under Warranty
    location: "Kitchen - Island",
    notes: "800 Series with CrystalDry technology and PrecisionWash system.",
    is_active: true,
    open_issue_count: 0,
    last_service_date: null,
  },
  {
    id: 4,
    name: "Central Heat Pump",
    brand: "Carrier",
    model_number: "25VNA836A003",
    category: "air_conditioner",
    purchase_date: "2022-03-05",
    warranty_expiry: "2032-03-05", // 10-year parts warranty
    location: "Exterior / Utility Room",
    notes: "Infinity 18VS Variable-Speed Heat Pump with Greenspeed Intelligence.",
    is_active: true,
    open_issue_count: 0,
    last_service_date: "2024-05-10",
  },
  {
    id: 5,
    name: "Countertop Microwave",
    brand: "Panasonic",
    model_number: "NN-SN966S",
    category: "microwave",
    purchase_date: "2023-11-28",
    warranty_expiry: "2024-11-28", // Expired recently
    location: "Kitchen Counter",
    notes: "2.2 cu ft Cyclonic Wave Inverter Technology 1250W.",
    is_active: true,
    open_issue_count: 0,
    last_service_date: null,
  }
];

export const MOCK_ISSUES = [
  {
    id: 101,
    appliance_id: 2,
    appliance_name: "Laundry Washer",
    appliance_brand: "Whirlpool",
    appliance_model: "WFW5620HW",
    appliance_location: "Basement Laundry",
    title: "Loud vibration during high-speed spin cycle",
    description: "The washer starts shaking violently and making a heavy thumping sound whenever the spin cycle exceeds 1000 RPM. Clothes come out slightly damp.",
    severity: "high",
    status: "investigating",
    reported_at: "2025-05-10T09:30:00Z",
    resolved_at: null,
    symptoms: [
      { id: 1, name: "Noise Level", value: "88", unit: "dB" },
      { id: 2, name: "Vibration Pattern", value: "Lateral oscillation during drain & spin", unit: null },
      { id: 3, name: "Drum Clearance", value: "Noticeable slack when rotating tub by hand", unit: null }
    ],
    recommended_checks: [
      "Verify shipping bolts have remained detached",
      "Inspect front and rear suspension damper struts for oil leakage",
      "Check cabinet levelness with 24-inch spirit level"
    ]
  },
  {
    id: 102,
    appliance_id: 1,
    appliance_name: "Kitchen Refrigerator",
    appliance_brand: "Samsung",
    appliance_model: "RF28R7351SR",
    appliance_location: "Kitchen - Main Floor",
    title: "Ice maker bucket frosting over and jamming",
    description: "Ice maker mechanism forms a thick frost crust along the auger assembly, preventing ice cubes from dropping into dispenser chute.",
    severity: "medium",
    status: "repair_recommended",
    reported_at: "2025-05-08T14:15:00Z",
    resolved_at: null,
    symptoms: [
      { id: 4, name: "Chamber Temp", value: "14", unit: "°F" },
      { id: 5, name: "Frost Type", value: "White crystalline frost around ice room seal", unit: null },
      { id: 6, name: "Error Code", value: "22E (Ice maker fan circuit)", unit: null }
    ],
    recommended_checks: [
      "Inspect silicone gasket around ice compartment housing for air leak",
      "Test auger motor resistance and check ice room drain tube"
    ]
  },
  {
    id: 103,
    appliance_id: 3,
    appliance_name: "Dishwasher",
    appliance_brand: "Bosch",
    appliance_model: "SHP78CM5N",
    appliance_location: "Kitchen - Island",
    title: "Drain pump cycle interrupted by E24 notification",
    description: "Cycle stops 3 minutes before finish with E24 error code. Water drained partially after manual reset.",
    severity: "low",
    status: "resolved",
    reported_at: "2025-04-02T18:00:00Z",
    resolved_at: "2025-04-03T11:20:00Z",
    symptoms: [
      { id: 7, name: "Error Code", value: "E24", unit: null },
      { id: 8, name: "Water Level", value: "1.5 inches in sump", unit: null }
    ],
    recommended_checks: [
      "Clear debris from non-return drain valve under cylindrical filter"
    ]
  }
];

export const MOCK_REPAIRS = [
  {
    id: 201,
    appliance_id: 3,
    appliance_name: "Dishwasher (Bosch SHP78CM5N)",
    issue_id: 103,
    repair_type: "User Maintenance / Valve Cleaning",
    description: "Removed cylindrical microfilter basket, popped off drain pump impeller white plastic cover, and cleared trapped lemon seed blocking impeller blades.",
    parts_replaced: "None (Cleaned existing assembly)",
    service_cost: 0.00,
    repair_date: "2025-04-03",
    outcome: "successful",
    notes: "Ran 60-minute test cycle with rinse agent; fully cleared E24 error code."
  },
  {
    id: 202,
    appliance_id: 1,
    appliance_name: "Kitchen Refrigerator (Samsung RF28R7351SR)",
    issue_id: null,
    repair_type: "OEM Warranty Service",
    description: "Authorized technician installed updated ice room silicone sealing gasket kit and reprogrammed main PCB defrost logic.",
    parts_replaced: "DA97-15217D Auger Assembly, DA81-05595A Seal Kit",
    service_cost: 0.00,
    repair_date: "2024-04-12",
    outcome: "successful",
    notes: "Covered 100% under manufacturer warranty campaign."
  },
  {
    id: 203,
    appliance_id: 2,
    appliance_name: "Laundry Washer (Whirlpool WFW5620HW)",
    issue_id: null,
    repair_type: "DIY Part Replacement",
    description: "Replaced degraded door boot bellow seal that had small tear at 6 o'clock position causing minor moisture weep.",
    parts_replaced: "W11106747 Door Bellow Gasket Seal",
    service_cost: 89.95,
    repair_date: "2023-08-19",
    outcome: "successful",
    notes: "Installed spring clamp using needle nose pliers. Drum seal water-tested for 3 cycles."
  },
  {
    id: 204,
    appliance_id: 4,
    appliance_name: "Central Heat Pump (Carrier 25VNA836A003)",
    issue_id: null,
    repair_type: "Preventative Seasonal Maintenance",
    description: "Annual HVAC technician service: cleaned outdoor condenser coils, checked 410A refrigerant subcooling, cleared condensate trap.",
    parts_replaced: "Filter element (16x25x4 MERV 11)",
    service_cost: 145.00,
    repair_date: "2024-05-10",
    outcome: "successful",
    notes: "Static pressure within nominal spec (0.48 in. w.g.)."
  }
];

export const MOCK_METRICS = {
  active_appliances: 5,
  open_issues: 2,
  repairs_in_progress: 1,
  upcoming_warranty_expiries: 1,
  completed_repairs: 4,
};

export const MOCK_ATTENTION_ITEMS = [
  {
    id: 1,
    type: "issue_critical",
    title: "High Vibration Fault Detected",
    appliance: "Whirlpool Washer (Basement)",
    urgency: "Immediate Action Recommended",
    description: "Severe cabinet rocking during spin cycle can damage tub bearing or floor structure.",
    actionText: "Investigate Vibration Issue",
    targetTab: "investigation",
    issueId: 101,
    applianceId: 2,
  },
  {
    id: 2,
    type: "warranty_expiring",
    title: "Manufacturer Warranty Expiring Soon",
    appliance: "Samsung Refrigerator (Kitchen)",
    urgency: "Expires in 22 Days (Oct 15, 2025)",
    description: "Open ice maker issue should be filed with Samsung service before factory warranty elapses.",
    actionText: "View Warranty & File Claim",
    targetTab: "appliances",
    applianceId: 1,
  }
];
