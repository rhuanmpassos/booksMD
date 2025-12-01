# Script PowerShell para deploy do backend BooksMD no EC2
# Execute: .\aws\deploy-ec2.ps1

Write-Host "🚀 Iniciando deploy do BooksMD Backend no EC2..." -ForegroundColor Green

# Verifica se AWS CLI está instalado
$awsCli = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsCli) {
    Write-Host "❌ AWS CLI não encontrado no PATH." -ForegroundColor Red
    Write-Host "Por favor, instale o AWS CLI ou adicione ao PATH." -ForegroundColor Yellow
    Write-Host "Download: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ AWS CLI encontrado: $($awsCli.Source)" -ForegroundColor Green

# 1. Obter VPC ID padrão
Write-Host "`n📋 Obtendo informações da VPC..." -ForegroundColor Cyan
$vpcId = aws ec2 describe-vpcs --query "Vpcs[?IsDefault==\`true\`].VpcId" --output text --region us-east-1
if (-not $vpcId) {
    $vpcId = aws ec2 describe-vpcs --query "Vpcs[0].VpcId" --output text --region us-east-1
}
Write-Host "VPC ID: $vpcId" -ForegroundColor Yellow

# 2. Obter Subnet ID
Write-Host "`n📋 Obtendo Subnet..." -ForegroundColor Cyan
$subnetId = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[0].SubnetId" --output text --region us-east-1
Write-Host "Subnet ID: $subnetId" -ForegroundColor Yellow

# 3. Obter AMI ID mais recente do Amazon Linux 2023
Write-Host "`n📋 Obtendo AMI mais recente do Amazon Linux 2023..." -ForegroundColor Cyan
$amiId = aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-2023*" "Name=architecture,Values=x86_64" --query "sort_by(Images, &CreationDate)[-1].ImageId" --output text --region us-east-1
Write-Host "AMI ID: $amiId" -ForegroundColor Yellow

# 4. Verificar se já existe Security Group
Write-Host "`n📋 Verificando Security Group..." -ForegroundColor Cyan
$sgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=booksmd-backend-sg" "Name=vpc-id,Values=$vpcId" --query "SecurityGroups[0].GroupId" --output text --region us-east-1

if (-not $sgId -or $sgId -eq "None") {
    Write-Host "Criando Security Group..." -ForegroundColor Yellow
    $sgId = aws ec2 create-security-group --group-name booksmd-backend-sg --description "Security group para BooksMD Backend" --vpc-id $vpcId --region us-east-1 --query "GroupId" --output text
    Write-Host "✅ Security Group criado: $sgId" -ForegroundColor Green
    
    # Adicionar regras ao Security Group
    Write-Host "Adicionando regras ao Security Group..." -ForegroundColor Yellow
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-east-1 | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region us-east-1 | Out-Null
    Write-Host "✅ Regras adicionadas (SSH: 22, HTTP: 8000)" -ForegroundColor Green
} else {
    Write-Host "✅ Security Group já existe: $sgId" -ForegroundColor Green
}

# 5. Verificar Key Pair
Write-Host "`n📋 Verificando Key Pairs..." -ForegroundColor Cyan
$keyPairs = aws ec2 describe-key-pairs --query "KeyPairs[*].KeyName" --output text --region us-east-1
Write-Host "Key Pairs disponíveis: $keyPairs" -ForegroundColor Yellow

if (-not $keyPairs) {
    Write-Host "⚠️  Nenhum Key Pair encontrado. Criando um novo..." -ForegroundColor Yellow
    $keyName = "booksmd-key-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    aws ec2 create-key-pair --key-name $keyName --query "KeyMaterial" --output text --region us-east-1 | Out-File -FilePath "$keyName.pem" -Encoding ASCII
    Write-Host "✅ Key Pair criado: $keyName" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANTE: Salve o arquivo $keyName.pem em local seguro!" -ForegroundColor Red
} else {
    $keyName = ($keyPairs -split "`t")[0]
    Write-Host "Usando Key Pair: $keyName" -ForegroundColor Yellow
}

# 6. Ler user-data.sh
Write-Host "`n📋 Preparando user-data..." -ForegroundColor Cyan
$userDataPath = Join-Path $PSScriptRoot "user-data.sh"
if (Test-Path $userDataPath) {
    $userDataContent = Get-Content $userDataPath -Raw -Encoding UTF8
    $userDataBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userDataContent))
    Write-Host "✅ User-data carregado" -ForegroundColor Green
} else {
    Write-Host "⚠️  user-data.sh não encontrado, usando vazio" -ForegroundColor Yellow
    $userDataBase64 = ""
}

# 7. Criar instância EC2
Write-Host "`n🚀 Criando instância EC2..." -ForegroundColor Cyan
Write-Host "Configuração:" -ForegroundColor Yellow
Write-Host "  - Tipo: t3.medium" -ForegroundColor Gray
Write-Host "  - AMI: $amiId" -ForegroundColor Gray
Write-Host "  - VPC: $vpcId" -ForegroundColor Gray
Write-Host "  - Subnet: $subnetId" -ForegroundColor Gray
Write-Host "  - Security Group: $sgId" -ForegroundColor Gray
Write-Host "  - Key Pair: $keyName" -ForegroundColor Gray

$instanceJson = aws ec2 run-instances `
    --image-id $amiId `
    --instance-type t3.medium `
    --key-name $keyName `
    --security-group-ids $sgId `
    --subnet-id $subnetId `
    --user-data $userDataBase64 `
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=booksmd-backend}]" `
    --region us-east-1 `
    --output json

$instanceId = ($instanceJson | ConvertFrom-Json).Instances[0].InstanceId
Write-Host "`n✅ Instância criada: $instanceId" -ForegroundColor Green

# 8. Aguardar instância estar rodando
Write-Host "`n⏳ Aguardando instância estar em execução..." -ForegroundColor Cyan
aws ec2 wait instance-running --instance-ids $instanceId --region us-east-1
Write-Host "✅ Instância em execução!" -ForegroundColor Green

# 9. Obter IP público
Write-Host "`n📋 Obtendo informações da instância..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$publicIp = aws ec2 describe-instances --instance-ids $instanceId --query "Reservations[0].Instances[0].PublicIpAddress" --output text --region us-east-1
$publicDns = aws ec2 describe-instances --instance-ids $instanceId --query "Reservations[0].Instances[0].PublicDnsName" --output text --region us-east-1

Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "✅ DEPLOY CONCLUÍDO!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "📋 Informações da Instância:" -ForegroundColor Cyan
Write-Host "  Instance ID: $instanceId" -ForegroundColor Yellow
Write-Host "  IP Público: $publicIp" -ForegroundColor Yellow
Write-Host "  DNS Público: $publicDns" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔗 URLs:" -ForegroundColor Cyan
Write-Host "  Backend: http://$publicIp:8000" -ForegroundColor Yellow
Write-Host "  Health Check: http://$publicIp:8000/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔐 Conectar via SSH:" -ForegroundColor Cyan
Write-Host "  ssh -i $keyName.pem ec2-user@$publicIp" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Aguarde ~2-3 minutos para o user-data configurar o servidor" -ForegroundColor Gray
Write-Host "  2. Conecte via SSH e verifique os logs: sudo journalctl -u booksmd -f" -ForegroundColor Gray
Write-Host "  3. Teste o endpoint: curl http://$publicIp:8000/health" -ForegroundColor Gray
Write-Host "  4. Atualize o frontend com a URL: http://$publicIp:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Lembre-se de configurar o CORS no backend com a URL do frontend:" -ForegroundColor Yellow
Write-Host "   https://booksmd.vercel.app" -ForegroundColor Gray
Write-Host ""

