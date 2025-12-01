# Script PowerShell para configurar HTTPS gratuito usando ALB + ACM
# O certificado SSL é gratuito, mas o ALB tem custo (~$16/mês)
# Para solução 100% gratuita, use o proxy no Vercel (já configurado)

$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$region = "us-east-1"
$vpcId = "vpc-00bb6172fea2134ff"
$subnetId = "subnet-04afd68f83118dd20"
$instanceId = "i-08325549fdbee150a"

Write-Host "🔒 Configurando HTTPS com Application Load Balancer..." -ForegroundColor Cyan
Write-Host "⚠️  ATENÇÃO: ALB tem custo de ~$16/mês" -ForegroundColor Yellow
Write-Host "💡 Para solução gratuita, use o proxy no vercel.json (já configurado)" -ForegroundColor Green
Write-Host ""

# 1. Criar Target Group
Write-Host "1. Criando Target Group..." -ForegroundColor Cyan
$tgResult = & $aws elbv2 create-target-group `
    --name booksmd-targets `
    --protocol HTTP `
    --port 8000 `
    --vpc-id $vpcId `
    --health-check-path /health `
    --health-check-interval-seconds 30 `
    --health-check-timeout-seconds 5 `
    --healthy-threshold-count 2 `
    --unhealthy-threshold-count 3 `
    --region $region `
    --output json | ConvertFrom-Json

$targetGroupArn = $tgResult.TargetGroups[0].TargetGroupArn
Write-Host "✅ Target Group criado: $targetGroupArn" -ForegroundColor Green

# 2. Registrar instância no Target Group
Write-Host "2. Registrando instância no Target Group..." -ForegroundColor Cyan
& $aws elbv2 register-targets `
    --target-group-arn $targetGroupArn `
    --targets Id=$instanceId `
    --region $region | Out-Null
Write-Host "✅ Instância registrada" -ForegroundColor Green

# 3. Criar Security Group para ALB
Write-Host "3. Criando Security Group para ALB..." -ForegroundColor Cyan
$albSgResult = & $aws ec2 create-security-group `
    --group-name booksmd-alb-sg `
    --description "Security group para ALB do BooksMD" `
    --vpc-id $vpcId `
    --region $region `
    --output json | ConvertFrom-Json

$albSgId = $albSgResult.GroupId

# Permitir HTTP e HTTPS
& $aws ec2 authorize-security-group-ingress `
    --group-id $albSgId `
    --protocol tcp `
    --port 80 `
    --cidr 0.0.0.0/0 `
    --region $region | Out-Null

& $aws ec2 authorize-security-group-ingress `
    --group-id $albSgId `
    --protocol tcp `
    --port 443 `
    --cidr 0.0.0.0/0 `
    --region $region | Out-Null

Write-Host "✅ Security Group criado: $albSgId" -ForegroundColor Green

# 4. Obter segunda subnet (ALB precisa de pelo menos 2)
Write-Host "4. Obtendo subnets..." -ForegroundColor Cyan
$subnets = & $aws ec2 describe-subnets `
    --filters "Name=vpc-id,Values=$vpcId" `
    --query 'Subnets[*].SubnetId' `
    --output text `
    --region $region

$subnetArray = $subnets -split "`t"
$subnet1 = $subnetArray[0]
$subnet2 = $subnetArray[1]

if (-not $subnet2) {
    Write-Host "⚠️  Apenas uma subnet encontrada. ALB precisa de pelo menos 2 subnets em zonas diferentes." -ForegroundColor Yellow
    Write-Host "Criando ALB com uma subnet apenas..." -ForegroundColor Yellow
    $subnet2 = $subnet1
}

# 5. Criar Application Load Balancer
Write-Host "5. Criando Application Load Balancer..." -ForegroundColor Cyan
$albResult = & $aws elbv2 create-load-balancer `
    --name booksmd-alb `
    --subnets $subnet1 $subnet2 `
    --security-groups $albSgId `
    --scheme internet-facing `
    --type application `
    --ip-address-type ipv4 `
    --region $region `
    --output json | ConvertFrom-Json

$albArn = $albResult.LoadBalancers[0].LoadBalancerArn
$albDns = $albResult.LoadBalancers[0].DNSName

Write-Host "✅ ALB criado: $albDns" -ForegroundColor Green

# 6. Criar listener HTTP (redireciona para HTTPS depois)
Write-Host "6. Criando listener HTTP..." -ForegroundColor Cyan
& $aws elbv2 create-listener `
    --load-balancer-arn $albArn `
    --protocol HTTP `
    --port 80 `
    --default-actions Type=forward,TargetGroupArn=$targetGroupArn `
    --region $region | Out-Null

Write-Host "✅ Listener HTTP criado" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ ALB CONFIGURADO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Informações:" -ForegroundColor Cyan
Write-Host "  ALB DNS: $albDns" -ForegroundColor Yellow
Write-Host "  Backend URL: http://$albDns" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Configure um domínio (opcional) ou use o DNS do ALB" -ForegroundColor Gray
Write-Host "2. Para HTTPS, crie certificado no ACM:" -ForegroundColor Gray
Write-Host "   aws acm request-certificate --domain-name seu-dominio.com --validation-method DNS --region $region" -ForegroundColor Gray
Write-Host "3. Depois de validado, crie listener HTTPS:" -ForegroundColor Gray
Write-Host "   aws elbv2 create-listener --load-balancer-arn $albArn --protocol HTTPS --port 443 --certificates CertificateArn=ARN --default-actions Type=forward,TargetGroupArn=$targetGroupArn" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 SOLUÇÃO GRATUITA: Use o proxy no vercel.json (já configurado)" -ForegroundColor Green
Write-Host "   O frontend já está configurado para usar same origin (proxy)" -ForegroundColor Gray
Write-Host ""

