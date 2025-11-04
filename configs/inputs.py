"""
Test Incident Reports for Incident Copilot
Contains example incident reports for testing the workflow with both complete and incomplete data.
"""

# Complete Incident Report 1 - CAN Bus DoS Attack
COMPLETE_REPORT_CAN_BUS = """
**Incident ID**: INC-2024-001
**Date of Detection**: 2024-01-15 14:32 UTC
**Vehicle ID**: AV-FLEET-4521
**Threat Category**: CAN Bus DoS Attack
**Severity**: High

**Detailed Incident Description**:
Unauthorized CAN bus messages were detected flooding the vehicle's internal network at a rate
of approximately 5,000 messages per second. The attack originated from a compromised OBD-II
diagnostic port that was left accessible after a recent maintenance session. The flooding caused
multiple Electronic Control Units (ECUs) to become unresponsive, including the brake controller,
steering assistance module, and battery management system. Vehicle safety systems were severely
degraded, triggering an emergency stop protocol.

**Impact Assessment**:
- High severity security incident affecting critical vehicle systems
- Multiple ECUs became unresponsive (brake controller, steering, BMS)
- Safety-critical autonomous driving functions disabled
- Vehicle entered emergency safe stop mode on highway
- No physical injuries reported
- Estimated downtime: 8 hours for system restoration
- One vehicle affected in the test fleet

**Response and Forensic Analysis**:
Security team immediately isolated the vehicle from fleet network. Forensic analysis revealed
the attack vector was an unsecured OBD-II port with default credentials. The attacker used a
commercially available CAN injection tool. All CAN bus traffic was logged and analyzed.

**Current Status**:
Attack has been stopped. Vehicle systems restored. Root cause identified. Implementing
mitigation measures across fleet. Incident contained but prevention measures needed.
"""

# Complete Incident Report 2 - GPS Spoofing Attack
COMPLETE_REPORT_GPS_SPOOFING = """
**Incident ID**: INC-2024-007
**Date of Detection**: 2024-02-03 09:15 UTC
**Vehicle ID**: AV-FLEET-8832
**Fleet**: Urban Delivery Fleet
**Threat Category**: GPS Spoofing Attack
**Detection Method**: Anomaly detection system
**Severity**: Medium
**Status**: Resolved

**Detailed Incident Description**:
A GPS spoofing attack was detected on February 3rd at 9:15 UTC affecting autonomous delivery
vehicle AV-FLEET-8832. The vehicle's navigation system received falsified GPS signals that
indicated it was 2.3 kilometers away from its actual location. The spoofed signals caused the
vehicle to recalculate its route multiple times and attempt to navigate to incorrect waypoints.
The attack was detected by the onboard sensor fusion system when GPS data conflicted with
LIDAR and visual odometry readings. The vehicle automatically engaged fail-safe mode and
requested remote operator assistance.

**Impact Assessment**:
- Medium severity - navigation system compromised but safety systems engaged properly
- One vehicle affected out of 45-vehicle urban delivery fleet
- No collision or safety incident occurred due to sensor fusion safety mechanisms
- Delivery route delayed by 35 minutes while under remote operator control
- Customer deliveries rescheduled
- Attack duration: approximately 12 minutes before detection and mitigation

**Response and Forensic Analysis**:
Upon detection, the vehicle immediately switched to lidar-based localization and requested
remote operator takeover. Signal analysis confirmed GPS spoofing via Software-Defined Radio
(SDR). The attack originated from a stationary location along the delivery route. Local
authorities were notified and are investigating. Vehicle logs showed consistent spoofing
pattern attempting to redirect vehicle off planned route.

**Lessons Learned and Recommendations**:
- Sensor fusion redundancy successfully prevented safety incident
- GPS-only navigation insufficient for autonomous vehicles in contested environments
- Deploy multi-constellation GNSS receivers (GPS, GLONASS, Galileo)
- Implement cryptographic GNSS authentication when available
- Enhance anomaly detection for GPS signal quality and consistency
- Consider RF spectrum monitoring for known spoofing signatures
"""

# Incomplete/Noisy Incident Report - Missing Critical Information
INCOMPLETE_REPORT_SUSPICIOUS_NETWORK = """
**Incident Report - Suspicious Network Activity**

There was some unusual network activity detected on one of our autonomous vehicles.
The security monitoring system flagged it as potentially suspicious.

Someone from the operations team noticed the vehicle was communicating with an external
IP address that wasn't on our approved list. 

**What we observed:**
- Traffic volume seemed higher than normal
- Some encrypted data was being transmitted

**Current Situation:**
Not really sure, The monitoring system is still collecting data. We're not sure if this is an actual
security incident or just a configuration issue. 

"""

# Dictionary for easy access
TEST_REPORTS = {
    'complete_can_bus': COMPLETE_REPORT_CAN_BUS,
    'complete_gps_spoofing': COMPLETE_REPORT_GPS_SPOOFING,
    'incomplete_network': INCOMPLETE_REPORT_SUSPICIOUS_NETWORK
}