# Frontend Issues

## High Priority Issues

### 1. Debug Console Logs in Production Code

**Description:**  
There are numerous debug console logs in production code. These logs are used for debugging but were not removed before deployment.

**Impact:**  
This clutters the browser console and potentially exposes sensitive information. It also impacts performance and makes it harder to debug real issues.

**Examples:**
- Console logs in the VM management page
- Debug logs showing API responses
- Logs showing component rendering cycles

**Code Example:**
```javascript
// Debug console logs in VM management page
console.log("Loading VMs...")
console.log("DB VMs response:", dbResponse)
console.log("Transforming VM:", vm)
console.log("About to render DataTable")
console.log("createColumns:", createColumns)
console.log("updateVMWhitelist:", updateVMWhitelist)
console.log("vms:", vms)
```

**Recommended Fix:**
- Remove all debug console logs from production code
- Implement proper logging that can be toggled in development
- Use a linting rule to prevent console logs in production
- Add a build step to strip console logs in production builds

### 2. Inconsistent Error Handling

**Description:**  
Error handling is inconsistent across components. Some components show detailed error messages, while others fail silently or show generic messages.

**Impact:**  
This leads to a poor user experience when errors occur. Users may not understand what went wrong or how to fix it.

**Examples:**
- Some components show detailed error messages
- Others show generic "Something went wrong" messages
- Some errors are not displayed to the user at all
- Inconsistent error UI (toasts, inline messages, etc.)

**Code Example:**
```javascript
// Detailed error handling
try {
  const response = await proxmoxNodesAPI.getNodes({ limit: 100 })
  // ...
} catch (err) {
  console.error("Error loading Proxmox Nodes:", err)
  setError("Failed to load Proxmox nodes")
  toast({
    title: "Error",
    description: "Failed to load Proxmox nodes",
    variant: "destructive"
  })
}

// Minimal error handling
try {
  const response = await vmsAPI.getVMs({ limit: 100 })
  // ...
} catch (err) {
  console.error("Error:", err)
}
```

**Recommended Fix:**
- Implement consistent error handling across all components
- Create reusable error handling utilities
- Use a consistent UI for displaying errors
- Add error boundaries to prevent cascading failures

### 3. Limited Form Validation

**Description:**  
Form validation is limited and inconsistent. Some forms validate input thoroughly, while others have minimal validation.

**Impact:**  
This can lead to data integrity issues and a poor user experience. Users may submit invalid data without realizing it.

**Examples:**
- Some forms validate input before submission
- Others rely on backend validation
- Inconsistent validation UI
- Missing validation for some fields

**Code Example:**
```javascript
// Limited validation in whitelist dialog
const handleAddVmid = () => {
  const vmid = parseInt(vmidInput.trim())
  if (isNaN(vmid) || vmid <= 0) {
    toast({
      title: "Error",
      description: "Please enter a valid VMID (positive number)",
      variant: "destructive",
    })
    return
  }
  // ...
}

// No client-side validation in add node dialog
const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  try {
    const response = await proxmoxNodesAPI.createNode({
      name,
      hostname,
      port: parseInt(port),
    })
    // ...
  } catch (error) {
    // ...
  }
}
```

**Recommended Fix:**
- Implement comprehensive form validation
- Use a form validation library (e.g., React Hook Form, Formik)
- Create reusable validation utilities
- Add inline validation feedback
- Validate all inputs before submission

## Medium Priority Issues

### 1. Inline Styles Instead of Design System

**Description:**  
Some components use inline styles instead of the design system. This leads to inconsistent UI and makes it harder to maintain the codebase.

**Impact:**  
This results in inconsistent UI and makes it harder to maintain the codebase. Changes to the design system may not be reflected in components with inline styles.

**Examples:**
- Inline styles for margins and padding
- Hardcoded colors instead of design system tokens
- Custom styling instead of using design system components

**Code Example:**
```jsx
// Inline styles
<div className="p-4 text-center text-red-500">
  {error}
  <Button
    variant="outline"
    size="sm"
    className="ml-2"
    onClick={handleRefresh}
    disabled={loading}
  >
    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
    Retry
  </Button>
</div>

// Custom styling instead of design system
<div style={{ marginTop: '10px', color: 'red' }}>
  Error message
</div>
```

**Recommended Fix:**
- Use design system components consistently
- Replace inline styles with design system tokens
- Create reusable UI components for common patterns
- Document design system usage

### 2. Inconsistent Loading States

**Description:**  
Loading states are inconsistent across components. Some components show loading indicators, while others don't.

**Impact:**  
This leads to a poor user experience during loading. Users may not know if an action is in progress or if something went wrong.

**Examples:**
- Some components show loading indicators
- Others don't indicate loading at all
- Inconsistent loading UI (spinners, skeletons, etc.)
- No loading indicators for some async operations

**Code Example:**
```jsx
// Loading indicator
{loading && vms.length === 0 ? (
  <div className="p-8 text-center">
    <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-muted-foreground" />
    <p className="text-sm text-muted-foreground">Loading virtual machines...</p>
  </div>
) : (
  // ...
)}

// No loading indicator
const handleSync = async (nodeId) => {
  try {
    const response = await proxmoxNodesAPI.syncNodeVMs(nodeId)
    // ...
  } catch (err) {
    // ...
  }
}
```

**Recommended Fix:**
- Implement consistent loading states across all components
- Create reusable loading components
- Add loading indicators for all async operations
- Use skeleton loaders for content that takes time to load

## Low Priority Issues

### 1. No Responsive Design for Some Components

**Description:**  
Some components don't have proper responsive design. They don't adapt well to different screen sizes.

**Impact:**  
This leads to a poor user experience on mobile devices and smaller screens.

**Examples:**
- Tables that overflow on small screens
- Fixed-width elements that cause horizontal scrolling
- Small touch targets on mobile
- Layout issues on small screens

**Code Example:**
```jsx
// Non-responsive table
<DataTable
  columns={columns}
  data={vms}
  filterColumn="name"
  filterPlaceholder="Filter by VM name..."
/>

// Fixed-width element
<div className="w-96">
  Content that won't adapt to screen size
</div>
```

**Recommended Fix:**
- Implement responsive design for all components
- Use responsive utilities (e.g., Tailwind's responsive classes)
- Test on different screen sizes
- Add mobile-specific UI where needed
