./scripts/demo-down.sh

# delete all workflows in localhost:7233
temporal workflow delete --query "WorkflowType != 'foo'" --yes

# delete all workflows in fde-oms-apps.sdvdw
temporal workflow delete --query "WorkflowType != 'foo'" --yes \
  --env fde-oms-apps

# delete all workflows in fde-oms-processing.sdvdw
temporal workflow delete --query "WorkflowType != 'foo'" --yes \
  --env fde-oms-processing

