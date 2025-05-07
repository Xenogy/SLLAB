# Basic Log Management

## Objective

Add simple management features to the log system to help with maintenance and provide basic insights.

## Tasks

### 1. Implement manual log cleanup

- Add a button in the admin interface to trigger log cleanup
- Show statistics about how many logs would be deleted
- Provide a confirmation dialog before deletion

#### Implementation Details

- Add a new section to the settings page at `/settings?tab=logs`
- Create a card component with log cleanup options:
  - Display current log count by level and age
  - Show estimated space usage
  - Provide a "Cleanup Logs" button
  - Include a "Dry Run" option to show what would be deleted without actually deleting

```tsx
// Example component structure
const LogCleanupCard = () => {
  const [dryRun, setDryRun] = useState(true);
  const [cleanupStats, setCleanupStats] = useState(null);
  
  const handleCleanup = async () => {
    // Implementation details
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Log Cleanup</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Display log statistics */}
        {/* Dry run toggle */}
        {/* Cleanup button */}
      </CardContent>
    </Card>
  );
};
```

- Connect to the existing `/logs/cleanup` API endpoint
- Add a loading state during cleanup
- Display results after cleanup completes

### 2. Add simple log statistics

- Display count of logs by level in the last 24 hours
- Show a simple bar chart of log volume by day
- Highlight any unusual patterns

#### Implementation Details

- Create a new component for the log statistics dashboard
- Add it to the logs page or a separate tab
- Implement two main visualizations:
  1. Log level distribution (pie chart or horizontal bar chart)
  2. Log volume over time (line chart or bar chart)

```tsx
// Example component structure
const LogStatistics = () => {
  const [timeRange, setTimeRange] = useState('24h');
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    // Fetch statistics when timeRange changes
  }, [timeRange]);
  
  return (
    <div>
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-bold">Log Statistics</h2>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectItem value="24h">Last 24 Hours</SelectItem>
          <SelectItem value="7d">Last 7 Days</SelectItem>
          <SelectItem value="30d">Last 30 Days</SelectItem>
        </Select>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Log level distribution chart */}
        {/* Log volume over time chart */}
      </div>
    </div>
  );
};
```

- Use the existing `/logs/statistics` API endpoint
- Implement automatic refresh (every 5 minutes or with a manual refresh button)
- Add a simple anomaly indicator (e.g., highlight days with unusually high error counts)

## Timeline

- Manual log cleanup implementation: 0.5-1 day
- Simple log statistics: 0.5-1 day
- Total estimated time: 1-2 days

## Dependencies

- Existing frontend framework and components
- Backend API endpoints for logs (already implemented)
- A charting library (e.g., Chart.js, Recharts)

## Success Criteria

- Administrators can easily clean up old logs
- Basic statistics provide insight into log patterns
- The interface is responsive and user-friendly
- Features integrate well with the existing UI
