# AL Test Repository for Serena

This repository contains AL (Application Language) code samples for testing the AL Language Server integration in Serena.

## Project Structure

```
test_repo/
├── app.json          # AL project configuration
├── src/              # Source code files
│   ├── Customer.Table.al           # Customer table definition
│   ├── CustomerCard.Page.al        # Customer card page
│   ├── CustomerList.Page.al        # Customer list page
│   ├── CustomerMgt.Codeunit.al     # Business logic codeunit
│   ├── CustomerType.Enum.al        # Enumeration type
│   ├── IPaymentProcessor.Interface.al  # Interface definition
│   ├── PaymentProcessorImpl.Codeunit.al # Interface implementation
│   └── Item.TableExt.al            # Table extension
└── .gitignore        # Git ignore file
```

## AL Language Constructs

This test repository demonstrates various AL language features:

### 1. Tables (`Customer.Table.al`)
- Field definitions with various data types
- Table keys (primary and secondary)
- Field groups for UI
- Table triggers (OnInsert, OnModify, OnDelete, OnRename)
- Procedures within tables
- FlowFields with CalcFormula

### 2. Pages (`CustomerCard.Page.al`, `CustomerList.Page.al`)
- Card and List page types
- Field controls with properties
- Actions and promoted actions
- Page triggers
- FactBoxes
- Style expressions

### 3. Codeunits (`CustomerMgt.Codeunit.al`)
- Procedures with parameters and return values
- Local and global variables
- Event subscribers
- Error handling
- Record manipulation

### 4. Enumerations (`CustomerType.Enum.al`)
- Enum values with captions
- Extensible enums

### 5. Interfaces (`IPaymentProcessor.Interface.al`)
- Interface procedures
- Interface implementation in codeunit

### 6. Table Extensions (`Item.TableExt.al`)
- Extending base tables
- Adding new fields
- Adding new keys
- Adding new procedures

## Testing Features

This repository is designed to test:

- **Symbol Discovery**: Finding tables, fields, procedures, enums, interfaces
- **Reference Finding**: Cross-file references between objects
- **Navigation**: Go-to-definition for types and procedures
- **Symbol Hierarchy**: Nested structures (procedures in codeunits, fields in tables)
- **Completion**: IntelliSense for AL keywords and symbols
- **Diagnostics**: Syntax and semantic error detection

## Dependencies

The code references standard Business Central objects:
- Item table (extended)
- Payment Terms table
- Currency table
- Customer Ledger Entry table
- Sales & Receivables Setup
- Various system codeunits

## Notes

This is a simplified test repository. In a real Business Central extension, you would need:
- Proper licensing
- Translation files
- Permission sets
- More comprehensive error handling
- Unit tests