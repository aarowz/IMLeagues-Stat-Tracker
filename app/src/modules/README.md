# Modules Directory

This folder contains functionality that needs to be accessible to the entire Streamlit application.

## Files

- `nav.py` - Custom navigation bar module that supports:
  - Sidebar navigation with role-based menu items
  - Role-Based Access Control (RBAC) functionality
  - User session state management
  - Navigation between pages based on user role

## Usage

The `nav.py` module is imported and called at the beginning of each page to ensure consistent navigation and access control across the application.
