const clusterProfiles = require("../fixtures/OsdAwsCcsCreatePublicCluster.json");
const clusterProperties = clusterProfiles["osdccs-aws-public"]["day1-profile"];

const clusterName = clusterProperties.ClusterName;
const awsAccountID = Cypress.env("QE_AWS_ID");
const awsAccessKey = Cypress.env("QE_AWS_ACCESS_KEY_ID");
const awsSecretKey = Cypress.env("QE_AWS_ACCESS_KEY_SECRET");

describe(
  "OSD AWS CCS Cluster - Create default public cluster with properties OCP-21086, OCP-21090)",
  { tags: ["day1", "osd", "aws", "public"] },
  () => {
    before(() => {
      cy.visit("/create");
    });
    it("Launch OSD AWS CCS cluster wizard", () => {
      CreateClusterPage.isCreateClusterPage();
      CreateOSDWizardPage.osdCreateClusterButton().click();
      CreateOSDWizardPage.isCreateOSDPage();
    });

    it("Step OSD - AWS CCS wizard Billing model", () => {
      CreateOSDWizardPage.isBillingModelScreen();
      CreateOSDWizardPage.selectSubscriptionType(
        clusterProperties.SubscriptionType
      );
      CreateOSDWizardPage.selectInfrastructureType(
        clusterProperties.InfrastructureType
      );
      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard - Cluster Settings - Select cloud provider definitions", () => {
      CreateOSDWizardPage.isCloudProviderSelectionScreen();
      CreateOSDWizardPage.selectCloudProvider(clusterProperties.CloudProvider);
      CreateOSDWizardPage.acknowlegePrerequisitesCheckbox().check();

      CreateOSDWizardPage.awsAccountIDInput().type(awsAccountID);
      CreateOSDWizardPage.awsAccessKeyInput().type(awsAccessKey);
      CreateOSDWizardPage.awsSecretKeyInput().type(awsSecretKey);

      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard - Cluster Settings - Select Cluster details definitions", () => {
      CreateOSDWizardPage.isClusterDetailsScreen();
      CreateOSDWizardPage.setClusterName(clusterName);
      CreateOSDWizardPage.closePopoverDialogs();
      if (clusterProperties.Availability.includes("Single zone")) {
        CreateOSDWizardPage.singleZoneAvilabilityRadio().check();
      } else {
        CreateOSDWizardPage.multiZoneAvilabilityRadio().check();
      }
      CreateOSDWizardPage.selectRegion(clusterProperties.Region);

      CreateOSDWizardPage.enableUserWorkloadMonitoringCheckbox().should(
        "be.checked"
      );

      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard - Cluster Settings - Select default machinepool definitions", () => {
      CreateOSDWizardPage.isMachinePoolScreen();
      CreateOSDWizardPage.selectComputeNodeType(
        clusterProperties.MachinePools[0].InstanceType
      );
      CreateOSDWizardPage.useBothIMDSv1AndIMDSv2Radio().should("be.checked");
      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard - Networking configuration - Select cluster privacy definitions", () => {
      CreateOSDWizardPage.isNetworkingScreen();
      CreateOSDWizardPage.selectClusterPrivacy(
        clusterProperties.ClusterPrivacy
      );
      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard CIDR Ranges - Select CIDR default values", () => {
      CreateOSDWizardPage.cidrDefaultValuesCheckBox().should("be.checked");
      CreateOSDWizardPage.useCIDRDefaultValues(false);
      CreateOSDWizardPage.useCIDRDefaultValues(true);
      CreateOSDWizardPage.machineCIDRInput().should(
        "have.value",
        clusterProperties.MachineCIDR
      );
      CreateOSDWizardPage.serviceCIDRInput().should(
        "have.value",
        clusterProperties.ServiceCIDR
      );
      CreateOSDWizardPage.podCIDRInput().should(
        "have.value",
        clusterProperties.PodCIDR
      );
      CreateOSDWizardPage.hostPrefixInput().should(
        "have.value",
        clusterProperties.HostPrefix
      );
      CreateOSDWizardPage.wizardNextButton().click();
    });

    it("Step OSD - AWS CCS wizard Cluster update - Select update strategies and its definitions", () => {
      CreateOSDWizardPage.isUpdatesScreen();
      CreateOSDWizardPage.updateStrategyIndividualRadio().should("be.checked");
      CreateOSDWizardPage.selectNodeDraining(clusterProperties.NodeDraining);
      CreateOSDWizardPage.wizardNextButton().click();
    });
  }
);
