# Recommended Work Orders for Optional Steps

**Date:** December 7, 2025  
**Purpose:** Document recommended work orders for optional enhancements

---

## Work Orders to Create

### 1. Add Terraform Configuration for Azure Key Vault

**Work Order Title:** Implement Azure Key Vault Infrastructure and Access Configuration

**Purpose:** Complete the Key Vault integration by creating the Key Vault resource and configuring access policies.

**Requirements:**
- Create Azure Key Vault resource via Terraform
- Configure access policies for Function App Managed Identity
- Store connection strings in Key Vault
- Update Function App configuration to reference Key Vault secrets
- Document Key Vault secret naming conventions

**Implementation Plan:**
- Create `iac/modules/key_vault/` module
- Add Key Vault resource to environment configurations
- Grant Function App Managed Identity access to Key Vault
- Update Function App app_settings to reference Key Vault secrets
- Create documentation for secret management

**Dependencies:**
- WO-15 (Key Vault client implementation) ✅ Complete
- WO-1 (Terraform infrastructure) ✅ Complete

**Estimated Effort:** 2-3 hours

---

### 2. Test Key Vault Integration with Managed Identity

**Work Order Title:** Test Azure Key Vault Integration with Managed Identity Authentication

**Purpose:** Validate that Key Vault integration works correctly with Managed Identity in Azure Functions.

**Requirements:**
- Deploy Function App with Managed Identity enabled
- Configure Key Vault access policies
- Store test secrets in Key Vault
- Verify Function App can retrieve secrets
- Test fallback to environment variables
- Document testing procedures

**Implementation Plan:**
- Deploy Function App to Azure (dev environment)
- Create Key Vault and store test secrets
- Configure Managed Identity access
- Run integration tests
- Verify secret retrieval
- Test error scenarios

**Dependencies:**
- WO-15 (Key Vault client) ✅ Complete
- Azure environment available
- Function App deployed

**Estimated Effort:** 2-3 hours

**Note:** Requires Azure environment

---

### 3. Enhance Metric Engine Clustering

**Work Order Title:** Enhance Metric Engine with Advanced Clustering and Analytics

**Purpose:** Improve Metric Engine capabilities with advanced clustering algorithms and analytics.

**Requirements:**
- Implement additional clustering algorithms
- Add anomaly detection capabilities
- Create clustering visualization
- Integrate clustering results into metrics
- Document clustering configuration

**Implementation Plan:**
- Review existing Clusterer implementation
- Add additional algorithms (DBSCAN, OPTICS, etc.)
- Implement anomaly detection
- Create visualization utilities
- Update MetricEngine to use enhanced clustering
- Add configuration options

**Dependencies:**
- WO-10 (Metric Engine) ✅ Complete
- WO-12 (Metric Engine Tests) ✅ Complete

**Estimated Effort:** 1-2 days

---

### 4. Add More Metric Rules

**Work Order Title:** Expand Metric Derivation Rules Library

**Purpose:** Add comprehensive metric derivation rules for compliance monitoring and analytics.

**Requirements:**
- Create additional metric rules for compliance (AML, KYC, PCI)
- Add business rule violation detection
- Create risk scoring rules
- Add fraud detection rules
- Document all rules

**Implementation Plan:**
- Review existing metric_rules.yaml
- Create compliance-specific rules
- Add business rule validation rules
- Implement risk scoring rules
- Add fraud detection patterns
- Update documentation

**Dependencies:**
- WO-10 (Metric Engine) ✅ Complete
- WO-14 (Metric Rules Configuration) - In backlog

**Estimated Effort:** 1-2 days

---

### 5. Fix YAML Parsing in metric_rules.yaml

**Work Order Title:** Fix YAML Parsing Issues in Metric Rules Configuration

**Purpose:** Resolve YAML parsing errors in metric_rules.yaml to enable full rule-based metric derivation.

**Requirements:**
- Fix YAML syntax errors in metric_rules.yaml
- Validate all rules parse correctly
- Test rule processing
- Update RuleProcessor error handling
- Document YAML format requirements

**Implementation Plan:**
- Review metric_rules.yaml syntax
- Fix YAML structure issues
- Validate with YAML parser
- Test RuleProcessor with fixed rules
- Update error messages
- Add YAML schema validation

**Dependencies:**
- WO-10 (Metric Engine) ✅ Complete
- WO-14 (Metric Rules Configuration) - In backlog

**Estimated Effort:** 1-2 hours

**Priority:** Medium (blocks full MetricEngine functionality)

---

### 6. Add Terraform Configuration for Database Schema Deployment

**Work Order Title:** Create Terraform Module for Database Schema Deployment

**Purpose:** Automate database schema deployment via Terraform instead of manual scripts.

**Requirements:**
- Create Terraform module for PostgreSQL schema deployment
- Integrate with existing database deployment scripts
- Support multiple environments
- Add schema versioning
- Document deployment process

**Implementation Plan:**
- Create `iac/modules/postgresql_schema/` module
- Use `postgresql` provider for schema management
- Integrate with existing SQL schema files
- Add version tracking
- Update deployment workflows

**Dependencies:**
- WO-34 (Database Schema) - In backlog
- WO-1 (Terraform infrastructure) ✅ Complete

**Estimated Effort:** 3-4 hours

---

## Priority Recommendations

### High Priority
1. **Fix YAML Parsing** (WO-5 above) - Blocks MetricEngine functionality
2. **Key Vault Terraform** (WO-1 above) - Completes WO-15 implementation

### Medium Priority
3. **Key Vault Testing** (WO-2 above) - Requires environment
4. **Database Schema Terraform** (WO-6 above) - Automation improvement

### Low Priority
5. **Enhanced Clustering** (WO-3 above) - Enhancement
6. **More Metric Rules** (WO-4 above) - Enhancement

---

## Work Order Details Template

For each work order above, use this template when creating in MCP:

```
Title: [Work Order Title]
Description: [Purpose]
Requirements:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

Implementation Plan:
- [Step 1]
- [Step 2]
- [Step 3]

Dependencies: [List dependencies]
Estimated Effort: [Time estimate]
```

---

## Notes

- These are optional enhancements
- Can be prioritized based on business needs
- Some require Azure environment availability
- All build on existing completed work

