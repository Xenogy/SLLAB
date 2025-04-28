# Frontend Architecture

## Overview

The frontend is built using Next.js, a React framework for building server-rendered applications. It provides a user interface for managing accounts, hardware profiles, and user authentication.

## Frontend Structure

### Pages

1. **Authentication**:
   - `/login`: User login page
   - `/register`: User registration page

2. **Dashboard**:
   - `/dashboard`: Main dashboard with account overview

3. **Accounts**:
   - `/accounts`: List of accounts
   - `/accounts/[id]`: Account details
   - `/accounts/new`: Create new account
   - `/accounts/upload`: Upload accounts from file

4. **Hardware**:
   - `/hardware`: List of hardware profiles
   - `/hardware/[id]`: Hardware profile details
   - `/hardware/new`: Create new hardware profile

5. **Cards**:
   - `/cards`: List of cards
   - `/cards/[id]`: Card details
   - `/cards/new`: Create new card

6. **Settings**:
   - `/settings`: User settings
   - `/settings/profile`: Profile settings
   - `/settings/security`: Security settings

### Components

1. **Layout Components**:
   - `Layout`: Main layout with navigation
   - `Sidebar`: Navigation sidebar
   - `Header`: Page header with user info

2. **Authentication Components**:
   - `LoginForm`: Login form
   - `RegisterForm`: Registration form
   - `PasswordResetForm`: Password reset form

3. **Account Components**:
   - `AccountList`: List of accounts
   - `AccountCard`: Account card component
   - `AccountForm`: Form for creating/editing accounts

4. **Hardware Components**:
   - `HardwareList`: List of hardware profiles
   - `HardwareCard`: Hardware card component
   - `HardwareForm`: Form for creating/editing hardware profiles

5. **Card Components**:
   - `CardList`: List of cards
   - `CardCard`: Card card component
   - `CardForm`: Form for creating/editing cards

6. **Utility Components**:
   - `Modal`: Modal dialog
   - `Notification`: Notification component
   - `Pagination`: Pagination component
   - `SearchBar`: Search bar component

### State Management

1. **Authentication State**:
   - Managed by `AuthProvider` context
   - Stores user information and token
   - Handles login, logout, and token refresh

2. **API State**:
   - Managed by custom hooks
   - Handles API requests and caching
   - Provides loading, error, and data states

## Authentication Flow

1. **Login**:
   - User enters credentials on login page
   - Frontend sends request to `/auth/token`
   - On success, token is stored in localStorage
   - User is redirected to dashboard

2. **Registration**:
   - User enters information on registration page
   - Frontend sends request to `/auth/register`
   - On success, user is redirected to login page

3. **Authenticated Requests**:
   - Token is included in Authorization header
   - Public endpoints are handled separately
   - Unauthorized responses trigger logout

## API Integration

1. **API Client**:
   - `api.ts` provides functions for API requests
   - Handles authentication and error handling
   - Provides typed responses for better type safety

2. **API Endpoints**:
   - `authAPI`: Authentication endpoints
   - `accountsAPI`: Account management endpoints
   - `hardwareAPI`: Hardware profile management endpoints
   - `cardsAPI`: Card management endpoints

## Current Issues and Improvement Areas

1. **Authentication Handling**:
   - Token storage in localStorage is vulnerable to XSS
   - No token refresh mechanism
   - Inconsistent handling of public endpoints

2. **Error Handling**:
   - Inconsistent error handling across components
   - Some errors are not properly displayed to the user

3. **State Management**:
   - No centralized state management solution
   - Prop drilling in some components

## Recommended Frontend Improvements

1. **Authentication Handling**:
   - Consider using HTTP-only cookies instead of localStorage
   - Implement token refresh mechanism
   - Improve handling of public endpoints

2. **Error Handling**:
   - Implement consistent error handling
   - Add proper error messages for all API errors
   - Add retry mechanism for failed requests

3. **State Management**:
   - Consider using a state management library (e.g., Redux, Zustand)
   - Implement proper caching for API responses
   - Reduce prop drilling with context or state management

4. **User Experience**:
   - Add loading states for all API requests
   - Improve form validation and error messages
   - Add confirmation dialogs for destructive actions

5. **Accessibility**:
   - Improve keyboard navigation
   - Add proper ARIA attributes
   - Ensure proper color contrast
