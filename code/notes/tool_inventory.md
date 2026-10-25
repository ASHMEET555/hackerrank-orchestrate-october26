# Available tool inventory

Exact function names exposed in this session. Use local filesystem/shell and patch tools for this repository, plus clock for timestamps and local image inspection for visual evidence. Use web only for useful public research; do not use connected apps for this local dataset task. No agent delegation is planned.

## Direct namespace tools

- `functions.exec`: run JavaScript orchestration and nested tools.
- `functions.wait`: resume a yielded exec call.
- `functions.request_user_input`: optional clarification in Plan mode (current mode is Default).
- `clock.sleep`: interruptible wait.
- `collaboration.spawn_agent`, `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `wait_agent`: agent delegation and coordination (not used).

## Nested tools (all exact exposed names)

### `apply_patch`

Make structured file edits.

`apply_patch`

### `clock`

General tool in the named namespace.

`clock__curr_time`

### `create_goal`

Start an explicitly requested persistent goal.

`create_goal`

### `exec_command`

Run shell commands in the workspace.

`exec_command`

### `get_goal`

Inspect the current goal.

`get_goal`

### `image_gen`

General tool in the named namespace.

`image_gen__imagegen`

### `list_mcp_resource_templates`

General tool in the named namespace.

`list_mcp_resource_templates`

### `list_mcp_resources`

General tool in the named namespace.

`list_mcp_resources`

### `mcp__codex_apps__codex_document_control_execute_document_command`

General tool in the named namespace.

`mcp__codex_apps__codex_document_control_execute_document_command`

### `mcp__codex_apps__codex_document_control_get_document_tool_schemas`

General tool in the named namespace.

`mcp__codex_apps__codex_document_control_get_document_tool_schemas`

### `mcp__codex_apps__codex_document_control_list_document_sessions`

General tool in the named namespace.

`mcp__codex_apps__codex_document_control_list_document_sessions`

### `mcp__codex_apps__notion_fetch`

General tool in the named namespace.

`mcp__codex_apps__notion_fetch`

### `mcp__codex_apps__notion_notion_calendar_cancel_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_cancel_events`

### `mcp__codex_apps__notion_notion_calendar_create_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_create_events`

### `mcp__codex_apps__notion_notion_calendar_list_calendar_resources`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_list_calendar_resources`

### `mcp__codex_apps__notion_notion_calendar_list_calendars`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_list_calendars`

### `mcp__codex_apps__notion_notion_calendar_list_contacts`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_list_contacts`

### `mcp__codex_apps__notion_notion_calendar_list_coworkers_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_list_coworkers_events`

### `mcp__codex_apps__notion_notion_calendar_list_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_list_events`

### `mcp__codex_apps__notion_notion_calendar_update_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_calendar_update_events`

### `mcp__codex_apps__notion_notion_check_mcp_next_steps`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_check_mcp_next_steps`

### `mcp__codex_apps__notion_notion_complete_mcp_setup`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_complete_mcp_setup`

### `mcp__codex_apps__notion_notion_connector_search`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_connector_search`

### `mcp__codex_apps__notion_notion_convert_page_to_skill`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_convert_page_to_skill`

### `mcp__codex_apps__notion_notion_create_attachment`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_attachment`

### `mcp__codex_apps__notion_notion_create_comment`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_comment`

### `mcp__codex_apps__notion_notion_create_database`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_database`

### `mcp__codex_apps__notion_notion_create_file_upload`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_file_upload`

### `mcp__codex_apps__notion_notion_create_folder`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_folder`

### `mcp__codex_apps__notion_notion_create_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_pages`

### `mcp__codex_apps__notion_notion_create_view`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_create_view`

### `mcp__codex_apps__notion_notion_delete_comment`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_delete_comment`

### `mcp__codex_apps__notion_notion_delete_databases`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_delete_databases`

### `mcp__codex_apps__notion_notion_delete_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_delete_pages`

### `mcp__codex_apps__notion_notion_download_attachment`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_download_attachment`

### `mcp__codex_apps__notion_notion_download_skill`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_download_skill`

### `mcp__codex_apps__notion_notion_duplicate_page`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_duplicate_page`

### `mcp__codex_apps__notion_notion_get_async_task`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_async_task`

### `mcp__codex_apps__notion_notion_get_comments`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_comments`

### `mcp__codex_apps__notion_notion_get_enabled_skills`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_enabled_skills`

### `mcp__codex_apps__notion_notion_get_file_download_urls`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_file_download_urls`

### `mcp__codex_apps__notion_notion_get_groups`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_groups`

### `mcp__codex_apps__notion_notion_get_self`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_self`

### `mcp__codex_apps__notion_notion_get_session_status`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_session_status`

### `mcp__codex_apps__notion_notion_get_teams`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_teams`

### `mcp__codex_apps__notion_notion_get_tool_access`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_tool_access`

### `mcp__codex_apps__notion_notion_get_users`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_get_users`

### `mcp__codex_apps__notion_notion_list_favorite_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_favorite_pages`

### `mcp__codex_apps__notion_notion_list_page_backlinks`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_page_backlinks`

### `mcp__codex_apps__notion_notion_list_private_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_private_pages`

### `mcp__codex_apps__notion_notion_list_recent_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_recent_pages`

### `mcp__codex_apps__notion_notion_list_session_events`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_session_events`

### `mcp__codex_apps__notion_notion_list_shared_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_list_shared_pages`

### `mcp__codex_apps__notion_notion_memory_search`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_memory_search`

### `mcp__codex_apps__notion_notion_move_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_move_pages`

### `mcp__codex_apps__notion_notion_query_meeting_notes`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_query_meeting_notes`

### `mcp__codex_apps__notion_notion_query_sessions`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_query_sessions`

### `mcp__codex_apps__notion_notion_read_session_event`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_read_session_event`

### `mcp__codex_apps__notion_notion_restore_pages`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_restore_pages`

### `mcp__codex_apps__notion_notion_search_agents`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_search_agents`

### `mcp__codex_apps__notion_notion_search_emails`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_search_emails`

### `mcp__codex_apps__notion_notion_search_sessions`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_search_sessions`

### `mcp__codex_apps__notion_notion_send_message_to_session`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_send_message_to_session`

### `mcp__codex_apps__notion_notion_set_comment_reaction`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_set_comment_reaction`

### `mcp__codex_apps__notion_notion_set_discussion_resolved`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_set_discussion_resolved`

### `mcp__codex_apps__notion_notion_show_advanced_analysis_next_steps`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_show_advanced_analysis_next_steps`

### `mcp__codex_apps__notion_notion_spawn_session`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_spawn_session`

### `mcp__codex_apps__notion_notion_stop_session`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_stop_session`

### `mcp__codex_apps__notion_notion_update_comment`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_comment`

### `mcp__codex_apps__notion_notion_update_data_source`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_data_source`

### `mcp__codex_apps__notion_notion_update_enabled_skills`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_enabled_skills`

### `mcp__codex_apps__notion_notion_update_folder`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_folder`

### `mcp__codex_apps__notion_notion_update_page`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_page`

### `mcp__codex_apps__notion_notion_update_view`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_update_view`

### `mcp__codex_apps__notion_notion_upload_skill`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_upload_skill`

### `mcp__codex_apps__notion_notion_view_thread_content`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_view_thread_content`

### `mcp__codex_apps__notion_notion_wait_session`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_wait_session`

### `mcp__codex_apps__notion_notion_xldb_add_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_add_column`

### `mcp__codex_apps__notion_notion_xldb_add_view_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_add_view_column`

### `mcp__codex_apps__notion_notion_xldb_add_view_join`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_add_view_join`

### `mcp__codex_apps__notion_notion_xldb_apply_rows`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_apply_rows`

### `mcp__codex_apps__notion_notion_xldb_apply_table`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_apply_table`

### `mcp__codex_apps__notion_notion_xldb_detach_view_data_source`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_detach_view_data_source`

### `mcp__codex_apps__notion_notion_xldb_get_column_optimization`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_column_optimization`

### `mcp__codex_apps__notion_notion_xldb_get_table_optimization_context`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_table_optimization_context`

### `mcp__codex_apps__notion_notion_xldb_get_table_schema`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_table_schema`

### `mcp__codex_apps__notion_notion_xldb_get_view`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_view`

### `mcp__codex_apps__notion_notion_xldb_get_view_joins`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_view_joins`

### `mcp__codex_apps__notion_notion_xldb_get_workspace_status`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_get_workspace_status`

### `mcp__codex_apps__notion_notion_xldb_list_tables`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_list_tables`

### `mcp__codex_apps__notion_notion_xldb_list_views`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_list_views`

### `mcp__codex_apps__notion_notion_xldb_optimize_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_optimize_column`

### `mcp__codex_apps__notion_notion_xldb_plan_table`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_plan_table`

### `mcp__codex_apps__notion_notion_xldb_query_rows`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_query_rows`

### `mcp__codex_apps__notion_notion_xldb_query_view_rows`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_query_view_rows`

### `mcp__codex_apps__notion_notion_xldb_remove_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_remove_column`

### `mcp__codex_apps__notion_notion_xldb_remove_view_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_remove_view_column`

### `mcp__codex_apps__notion_notion_xldb_remove_view_join`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_remove_view_join`

### `mcp__codex_apps__notion_notion_xldb_unoptimize_column`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_unoptimize_column`

### `mcp__codex_apps__notion_notion_xldb_update_column_title`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_update_column_title`

### `mcp__codex_apps__notion_notion_xldb_update_view_join`

General tool in the named namespace.

`mcp__codex_apps__notion_notion_xldb_update_view_join`

### `mcp__codex_apps__notion_query_data_sources`

General tool in the named namespace.

`mcp__codex_apps__notion_query_data_sources`

### `mcp__codex_apps__notion_query_multiple_data_sources`

General tool in the named namespace.

`mcp__codex_apps__notion_query_multiple_data_sources`

### `mcp__codex_apps__notion_search`

General tool in the named namespace.

`mcp__codex_apps__notion_search`

### `mcp__codex_apps__pets_adopt`

General tool in the named namespace.

`mcp__codex_apps__pets_adopt`

### `mcp__codex_apps__pets_create_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_create_pet`

### `mcp__codex_apps__pets_delete_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_delete_pet`

### `mcp__codex_apps__pets_get_pet_download_link`

General tool in the named namespace.

`mcp__codex_apps__pets_get_pet_download_link`

### `mcp__codex_apps__pets_list_pets`

General tool in the named namespace.

`mcp__codex_apps__pets_list_pets`

### `mcp__codex_apps__pets_prepare_pet_upload`

General tool in the named namespace.

`mcp__codex_apps__pets_prepare_pet_upload`

### `mcp__codex_apps__pets_select_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_select_pet`

### `mcp__codex_apps__pets_share_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_share_pet`

### `mcp__codex_apps__pets_unshare_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_unshare_pet`

### `mcp__codex_apps__pets_update_pet`

General tool in the named namespace.

`mcp__codex_apps__pets_update_pet`

### `mcp__codex_apps__pets_validate_pet_spritesheet`

General tool in the named namespace.

`mcp__codex_apps__pets_validate_pet_spritesheet`

### `mcp__codex_apps__plugin_management_get_app_permissions`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_get_app_permissions`

### `mcp__codex_apps__plugin_management_get_plugin_dependencies`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_get_plugin_dependencies`

### `mcp__codex_apps__plugin_management_search_plugins`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_search_plugins`

### `mcp__codex_apps__plugin_management_suggest_plugins`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_suggest_plugins`

### `mcp__codex_apps__plugin_management_uninstall_app`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_uninstall_app`

### `mcp__codex_apps__plugin_management_update_app_permissions`

General tool in the named namespace.

`mcp__codex_apps__plugin_management_update_app_permissions`

### `mcp__codex_apps__safety_settings_get_family_info`

General tool in the named namespace.

`mcp__codex_apps__safety_settings_get_family_info`

### `mcp__codex_apps__safety_settings_get_parental_controls`

General tool in the named namespace.

`mcp__codex_apps__safety_settings_get_parental_controls`

### `mcp__codex_apps__safety_settings_get_trusted_contact`

General tool in the named namespace.

`mcp__codex_apps__safety_settings_get_trusted_contact`

### `mcp__codex_apps__safety_settings_prepare_parental_control_update`

General tool in the named namespace.

`mcp__codex_apps__safety_settings_prepare_parental_control_update`

### `mcp__codex_apps__safety_settings_update_parental_control`

General tool in the named namespace.

`mcp__codex_apps__safety_settings_update_parental_control`

### `mcp__codex_apps__search_service_web_run`

General tool in the named namespace.

`mcp__codex_apps__search_service_web_run`

### `read_mcp_resource`

General tool in the named namespace.

`read_mcp_resource`

### `update_goal`

Update the current goal's status.

`update_goal`

### `view_image`

Inspect a local image.

`view_image`

### `web`

General tool in the named namespace.

`web__run`

### `write_stdin`

Interact with an active shell process.

`write_stdin`
