# Script para criar instancia EC2 do BooksMD Backend
$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$region = "us-east-1"

# Configuracoes
$vpcId = "vpc-00bb6172fea2134ff"
$subnetId = "subnet-04afd68f83118dd20"
$sgId = "sg-0e3e80528a9e9f2ba"
$amiId = "ami-0fa3fe0fa7920f68e"
$keyName = "booksmd-backend-key"
$instanceType = "t3.small"

# Preparar user-data
Write-Host "Preparando user-data..." -ForegroundColor Cyan
$userDataPath = Join-Path $PSScriptRoot "user-data.sh"
$userDataContent = Get-Content $userDataPath -Raw -Encoding UTF8
$userDataContent = $userDataContent -replace 'seu-usuario', 'rhuanmpassos'
$userDataContent = $userDataContent -replace 'CORS_ORIGINS=\*', 'CORS_ORIGINS=https://booksmd.vercel.app,https://booksmd.vercel.app/*'
$bytes = [System.Text.Encoding]::UTF8.GetBytes($userDataContent)
$base64 = [Convert]::ToBase64String($bytes)

# Criar instancia
Write-Host "Criando instancia EC2..." -ForegroundColor Cyan
$blockDeviceMapping = '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]'
$tags = 'ResourceType=instance,Tags=[{Key=Name,Value=booksmd-backend}]'

$result = & $aws ec2 run-instances `
    --image-id $amiId `
    --instance-type $instanceType `
    --key-name $keyName `
    --security-group-ids $sgId `
    --subnet-id $subnetId `
    --user-data $base64 `
    --block-device-mappings $blockDeviceMapping `
    --tag-specifications $tags `
    --region $region `
    --output json

$instanceJson = $result | ConvertFrom-Json
$instanceId = $instanceJson.Instances[0].InstanceId

Write-Host ""
Write-Host "SUCCESS: Instancia criada: $instanceId" -ForegroundColor Green
Write-Host "Aguardando instancia estar em execucao..." -ForegroundColor Cyan

# Aguardar instancia estar rodando
& $aws ec2 wait instance-running --instance-ids $instanceId --region $region

# Obter IP publico
Start-Sleep -Seconds 5
$publicIp = & $aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region $region
$publicDns = & $aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].PublicDnsName' --output text --region $region

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "DEPLOY CONCLUIDO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Informacoes:" -ForegroundColor Cyan
Write-Host "  Instance ID: $instanceId" -ForegroundColor Yellow
Write-Host "  IP Publico: $publicIp" -ForegroundColor Yellow
Write-Host "  DNS: $publicDns" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend URL: http://$publicIp:8000" -ForegroundColor Green
Write-Host "Health Check: http://$publicIp:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "SSH: ssh -i ..\booksmd-backend-key.pem ec2-user@$publicIp" -ForegroundColor Yellow
Write-Host ""
Write-Host "Aguarde ~3-5 minutos para o user-data configurar o servidor" -ForegroundColor Yellow
Write-Host "Verifique logs: ssh -i ..\booksmd-backend-key.pem ec2-user@$publicIp 'sudo journalctl -u booksmd -f'" -ForegroundColor Gray
