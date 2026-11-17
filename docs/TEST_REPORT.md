# CAR application test report

Scope: current local eroview working tree, not a verified copy of the client delivery-v1 checkout.

Automated local tests: 59 PASS. These use controlled inputs and mocked external services.
Live Chrome headless checks: 2 FAIL, 2 NOT RUN. Coordinate service returned HTTP 500 for both known samples.
No production source code was changed in this testing task.

## Local cases

1. PASS — `test_car_api.LookupTests.test_bad_responses_fail_without_fallback`
2. PASS — `test_car_api.LookupTests.test_different_property_is_rejected`
3. PASS — `test_car_api.LookupTests.test_exact_coordinates_and_registration`
4. PASS — `test_car_api.LookupTests.test_formatted_code_matches`
5. PASS — `test_car_api.LookupTests.test_invalid_coordinates_make_no_request`
6. PASS — `test_car_api.LookupTests.test_wrong_search_response_never_opens_details`
7. PASS — `test_car_api.LookupTests.test_wrong_visible_details_are_rejected_even_when_response_matches`
8. PASS — `test_coordinates.CoordinateTests.test_decimal_and_sign`
9. PASS — `test_coordinates.CoordinateTests.test_invalid`
10. PASS — `test_coordinates.CoordinateTests.test_sample_dms`
11. PASS — `test_diagnostics.DiagnosticsTests.test_restricted_endpoints`
12. PASS — `test_diagnostics.DiagnosticsTests.test_tokens_and_urls_not_logged`
13. PASS — `test_downloads.DownloadTests.test_error_response_preserves_existing_file_and_cleans_partial`
14. PASS — `test_downloads.DownloadTests.test_invalid_identifier_never_requests`
15. PASS — `test_downloads.DownloadTests.test_valid_zip_saved_with_progress`
16. PASS — `test_gui.GuiTests.test_cancel_returns_without_session_question`
17. PASS — `test_gui.GuiTests.test_closed_browser_no_exits`
18. PASS — `test_gui.GuiTests.test_closed_browser_yes_restores_form`
19. PASS — `test_gui.GuiTests.test_default_preferences_use_project_config`
20. PASS — `test_gui.GuiTests.test_failure_allows_retry`
21. PASS — `test_gui.GuiTests.test_invalid_input_never_starts_worker`
22. PASS — `test_gui.GuiTests.test_preference_restored_and_errors_localized`
23. PASS — `test_gui.GuiTests.test_statement_only_opens_verified_session_registration`
24. PASS — `test_gui.GuiTests.test_switch_during_loading_preserves_input_and_state`
25. PASS — `test_gui.GuiTests.test_translation_keys_match`
26. PASS — `test_gui.GuiTests.test_worker_launches_from_project_root_as_module`
27. PASS — `test_regressions.ApiRegressionTests.test_id_origin_preserved_with_registration`
28. PASS — `test_regressions.ApiRegressionTests.test_invalid_id_disables_download_identity`
29. PASS — `test_regressions.ApiRegressionTests.test_invalid_json_disposes_response`
30. PASS — `test_regressions.ApiRegressionTests.test_network_failure_is_explicit`
31. PASS — `test_regressions.CoordinateBoundaryTests.test_comma_decimal`
32. PASS — `test_regressions.CoordinateBoundaryTests.test_conflicting_sign`
33. PASS — `test_regressions.CoordinateBoundaryTests.test_empty`
34. PASS — `test_regressions.CoordinateBoundaryTests.test_infinity`
35. PASS — `test_regressions.CoordinateBoundaryTests.test_invalid_axis`
36. PASS — `test_regressions.CoordinateBoundaryTests.test_latitude_north_limit`
37. PASS — `test_regressions.CoordinateBoundaryTests.test_latitude_south_limit`
38. PASS — `test_regressions.CoordinateBoundaryTests.test_longitude_east_limit`
39. PASS — `test_regressions.CoordinateBoundaryTests.test_longitude_west_limit`
40. PASS — `test_regressions.CoordinateBoundaryTests.test_minutes_overflow`
41. PASS — `test_regressions.CoordinateBoundaryTests.test_nan`
42. PASS — `test_regressions.CoordinateBoundaryTests.test_north_overflow`
43. PASS — `test_regressions.CoordinateBoundaryTests.test_seconds_overflow`
44. PASS — `test_regressions.CoordinateBoundaryTests.test_southern_dms`
45. PASS — `test_regressions.CoordinateBoundaryTests.test_west_overflow`
46. PASS — `test_regressions.CoordinateBoundaryTests.test_western_dms`
47. PASS — `test_regressions.CoordinateBoundaryTests.test_wrong_hemisphere`
48. PASS — `test_regressions.CoordinateBoundaryTests.test_zero`
49. PASS — `test_regressions.DownloadFailureTests.test_certificate_error_no_insecure_retry`
50. PASS — `test_regressions.DownloadFailureTests.test_empty_zip_is_rejected`
51. PASS — `test_regressions.DownloadFailureTests.test_http_403_no_retry_loop`
52. PASS — `test_regressions.DownloadFailureTests.test_http_500_preserves_file`
53. PASS — `test_regressions.DownloadFailureTests.test_replace_permission_error_cleans_partial`
54. PASS — `test_regressions.DownloadFailureTests.test_timeout_preserves_file`
55. PASS — `test_regressions.PortalRegressionTests.test_client_ms_mismatch_after_click_is_blocked`
56. PASS — `test_regressions.PortalRegressionTests.test_matching_details_release_download_identity`
57. PASS — `test_report_links.ReportTests.test_invalid_registration_does_not_launch`
58. PASS — `test_report_links.ReportTests.test_normal_chrome_has_no_automation_or_profile_flags`
59. PASS — `test_report_links.ReportTests.test_url_uses_selected_registration`

## Live cases

- PR-client browser match: FAIL — Coordinate lookup returned HTTP 500.
- PR-client physical ZIP save: NOT RUN — Property not verified
- AM-sample browser match: FAIL — Coordinate lookup returned HTTP 500.
- AM-sample physical ZIP save: NOT RUN — Property not verified

## Acceptance checks still required

- Reproduce the client MS mismatch using the exact input coordinates and delivery-v1 revision; the screenshots provide CAR codes, not the input coordinates.
- Test download on the client certificate trust environment. The local certificate regression verifies safe failure, not a repair of that environment.
- Repeat successful complete browser searches across multiple properties and municipalities when the lookup service recovers.
- Test normal Chrome statement opening and manual CAPTCHA flow on the client machine. Headless tests do not validate CAPTCHA behavior.
- Verify real desktop save dialog, language switching, and successful/failed download messages manually.

## Run again

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/live_checks.py
```

Run these commands from the eroview project folder. Live checks contact the site and download to temporary folders, removed after verification.

## Independent comparison and repeat

- An independent urllib request for PR coordinates returned HTTP 200 and the expected C99A registration.
- Repeating the live Playwright flow returned HTTP 500 again for both PR and AM.
- This is a reproducible difference between request paths in this environment, not evidence of a general service outage. Root cause remains undiagnosed.
- Total distinct scenarios: 64 (59 local, 4 live flow scenarios, 1 independent API comparison). Repeated runs are not counted as new scenarios.
