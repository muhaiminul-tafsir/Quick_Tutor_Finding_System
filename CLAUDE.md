# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build
`dotnet build`

### Linting
`dotnet format`

### Testing
`dotnet test`
To run a single test file, use `dotnet test <path/to/testfile.cs>`.

## Code Architecture

The system is structured around an online tutor management concept, likely involving a layered approach with separate concerns for data management, business logic, and presentation.

1.  **Data Layer:** Responsible for all persistence operations, likely interacting with a database (e.g., EF Core context, repositories).
2.  **Business Logic Layer:** Contains the core tutoring logic and rules. This layer orchestrates data access and enforces business constraints.
3.  **Service Layer:** Coordinates operations between the Data and Business layers, potentially handling complex transaction flows.
4.  **Presentation Layer:** Handles input/output, likely involving controllers or UI components to interact with the services.

Review the existing files in the directory to refine this architecture based on the actual file structure.