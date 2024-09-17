Use managed identity to pull image from Azure Container Registry
Use the following steps to configure your web app to pull from Azure Container Registry (ACR) using managed identity. The steps use system-assigned managed identity, but you can use user-assigned managed identity as well.

Enable the system-assigned managed identity for the web app by using the az webapp identity assign command:

Azure CLI

Copy

Open Cloud Shell
az webapp identity assign --resource-group <group-name> --name <app-name> --query principalId --output tsv
Replace <app-name> with the name you used in the previous step. The output of the command (filtered by the --query and --output arguments) is the service principal ID of the assigned identity.

Get the resource ID of your Azure Container Registry:

Azure CLI

Copy

Open Cloud Shell
az acr show --resource-group <group-name> --name <registry-name> --query id --output tsv
Replace <registry-name> with the name of your registry. The output of the command (filtered by the --query and --output arguments) is the resource ID of the Azure Container Registry.

Grant the managed identity permission to access the container registry:

Azure CLI

Copy

Open Cloud Shell
az role assignment create --assignee <principal-id> --scope <registry-resource-id> --role "AcrPull"
Replace the following values:

<principal-id> with the service principal ID from the az webapp identity assign command
<registry-resource-id> with the ID of your container registry from the az acr show command
For more information about these permissions, see What is Azure role-based access control.

Configure your app to use the managed identity to pull from Azure Container Registry.

Azure CLI

Copy

Open Cloud Shell
az webapp config set --resource-group <group-name> --name <app-name> --generic-configurations '{"acrUseManagedIdentityCreds": true}'
Replace the following values:

<app-name> with the name of your web app.
 Tip

If you are using PowerShell console to run the commands, you need to escape the strings in the --generic-configurations argument in this and the next step. For example: --generic-configurations '{\"acrUseManagedIdentityCreds\": true'

(Optional) If your app uses a user-assigned managed identity, make sure the identity is configured on the web app and then set the acrUserManagedIdentityID property to specify its client ID:

Azure CLI

Copy

Open Cloud Shell
az identity show --resource-group <group-name> --name <identity-name> --query clientId --output tsv
Replace the <identity-name> of your user-assigned managed identity and use the output <client-id> to configure the user-assigned managed identity ID.

Azure CLI

Copy

Open Cloud Shell
az  webapp config set --resource-group <group-name> --name <app-name> --generic-configurations '{"acrUserManagedIdentityID": "<client-id>"}'
You're all set, and the web app now uses managed identity to pull from Azure Container Registry.