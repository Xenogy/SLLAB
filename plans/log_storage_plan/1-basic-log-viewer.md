# Basic Log Viewer UI

## Objective

Create a simple, functional log viewer page in the existing frontend.

## Tasks

### 1. Create a basic log listing page

- Add a new page at `/logs` that displays logs in a table format
- Include columns for:
  - Timestamp
  - Level (with color coding)
  - Category
  - Source
  - Message (truncated if too long)
- Implement simple pagination (previous/next buttons)
- Add a refresh button to update the log list

#### Implementation Details

- Create a new page component in `frontend/nextjs/app/(authenticated)/logs/page.tsx`
- Use the existing API client to fetch logs from the backend
- Implement a simple table component for displaying logs
- Use color coding for different log levels:
  - ERROR: Red (#dc3545)
  - WARNING: Yellow (#ffc107)
  - INFO: Blue (#0d6efd)
  - DEBUG: Gray (#6c757d)
  - CRITICAL: Dark Red (#7f0000)

### 2. Add essential filters

- Create a simple filter panel above the log table
- Include the following filters:
  - Date range picker (last hour, day, week, custom)
  - Log level dropdown (ERROR, WARNING, INFO, etc.)
  - Category dropdown (populated from available categories)
  - Source dropdown (populated from available sources)
  - Simple text search for messages
- Add a "Clear Filters" button to reset all filters

#### Implementation Details

- Use existing UI components for filters (dropdowns, date pickers, etc.)
- Implement client-side state management for filter values
- Update the API request parameters when filters change
- Store filter preferences in local storage for persistence

### 3. Implement log detail view

- Add a modal that shows when clicking on a log entry
- Display all log details including:
  - All basic fields (timestamp, level, category, source, message)
  - Entity information (type and ID)
  - User information
  - Trace information (trace ID, span ID)
  - JSON details in a formatted, collapsible view
- Add a "Copy to Clipboard" button for easy sharing

#### Implementation Details

- Create a modal component for displaying log details
- Use a JSON formatter component for displaying structured data
- Implement a copy-to-clipboard function for sharing log details

## Timeline

- Basic log listing page: 1 day
- Essential filters: 0.5-1 day
- Log detail view: 0.5-1 day
- Total estimated time: 2-3 days

## Dependencies

- Existing frontend framework and components
- Backend API endpoints for logs (already implemented)

## Success Criteria

- Users can view logs in a simple, readable format
- Basic filtering allows users to find relevant logs
- Log details are accessible and well-formatted
- The interface is responsive and performs well with large log volumes
