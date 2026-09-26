# Current limitations

The foundation works offline with bundled fictional satellite and sonar imagery and user-uploaded PNG/JPEG files. The satellite change mask is a classical pixel-difference baseline, **not learned change detection**; it can react to misregistration, lighting, water, and seasonal differences and cannot identify disaster damage. Uploaded sonar analysis flags bright regions only and is **not object classification**. Bundled sonar boxes are authored demo annotations, not detections. There is no real sonar hardware connection, trained sonar model, live feed, sonar geolocation, or sonar-to-hazard automation.

Cyclone Varuna's grid, routes, hazards, distances, satellite images, and sonar replay are simulated. There is no real geographic map or geographic routing yet; grid locations and 50 m cell distances are modeled, not measured positions. No Sentinel integration, real ocean provider, or GEBCO integration exists. External provider adapters return `NOT_CONFIGURED`. `REAL_DATA` and `OFFLINE_CACHED` are mission metadata modes only. Risk weights, thresholds, and routing are academic assumptions. Manual hazard certainty is user-entered; there is no authentication or verified operator identity.

The mission report is a current on-demand summary, not a signed audit record or saved historical snapshot. Uploaded files are held in a local image cache, not a managed object store. The report's statistics inherit the limitations of their source data and methods.

BLUE-RESCUE AI is an academic decision-support prototype. It is not a certified maritime navigation or emergency-response system. Operational deployment would require hydrographic validation, calibrated sensors, validated models and qualified maritime authorities.
