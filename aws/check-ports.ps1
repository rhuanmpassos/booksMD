# Script para verificar e configurar portas do Security Group do EC2
$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$region = "us-east-1"
$sgId = "sg-0e3e80528a9e9f2ba"

Write-Host "🔍 Verificando Security Group: $sgId" -ForegroundColor Cyan
Write-Host ""

# Verificar regras de entrada
Write-Host "📥 Regras de ENTRADA (Ingress):" -ForegroundColor Yellow
$ingressRules = & $aws ec2 describe-security-groups `
    --group-ids $sgId `
    --query 'SecurityGroups[0].IpPermissions' `
    --region $region `
    --output json | ConvertFrom-Json

if ($ingressRules.Count -eq 0) {
    Write-Host "  ⚠️  Nenhuma regra de entrada encontrada!" -ForegroundColor Red
} else {
    foreach ($rule in $ingressRules) {
        $port = $rule.FromPort
        $protocol = $rule.IpProtocol
        $cidr = $rule.IpRanges[0].CidrIp
        Write-Host "  ✅ Porta $port ($protocol) - Origem: $cidr" -ForegroundColor Green
    }
}

Write-Host ""

# Verificar se porta 8000 está aberta
$port8000Open = $ingressRules | Where-Object { $_.FromPort -eq 8000 -and $_.IpProtocol -eq 'tcp' }

if (-not $port8000Open) {
    Write-Host "⚠️  Porta 8000 (HTTP) NÃO está aberta!" -ForegroundColor Red
    Write-Host "🔧 Abrindo porta 8000..." -ForegroundColor Yellow
    
    & $aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 8000 `
        --cidr 0.0.0.0/0 `
        --region $region | Out-Null
    
    Write-Host "✅ Porta 8000 aberta para 0.0.0.0/0" -ForegroundColor Green
} else {
    Write-Host "✅ Porta 8000 (HTTP) já está aberta" -ForegroundColor Green
}

Write-Host ""

# Verificar se porta 22 está aberta
$port22Open = $ingressRules | Where-Object { $_.FromPort -eq 22 -and $_.IpProtocol -eq 'tcp' }

if (-not $port22Open) {
    Write-Host "⚠️  Porta 22 (SSH) NÃO está aberta!" -ForegroundColor Red
    Write-Host "🔧 Abrindo porta 22..." -ForegroundColor Yellow
    
    & $aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 22 `
        --cidr 0.0.0.0/0 `
        --region $region | Out-Null
    
    Write-Host "✅ Porta 22 aberta para 0.0.0.0/0" -ForegroundColor Green
} else {
    Write-Host "✅ Porta 22 (SSH) já está aberta" -ForegroundColor Green
}

Write-Host ""
Write-Host "📤 Regras de SAÍDA (Egress):" -ForegroundColor Yellow
$egressRules = & $aws ec2 describe-security-groups `
    --group-ids $sgId `
    --query 'SecurityGroups[0].IpPermissionsEgress' `
    --region $region `
    --output json | ConvertFrom-Json

if ($egressRules.Count -eq 0) {
    Write-Host "  ⚠️  Nenhuma regra de saída encontrada!" -ForegroundColor Red
} else {
    foreach ($rule in $egressRules) {
        if ($rule.FromPort) {
            $port = $rule.FromPort
            $protocol = $rule.IpProtocol
            $cidr = $rule.IpRanges[0].CidrIp
            Write-Host "  ✅ Porta $port ($protocol) - Destino: $cidr" -ForegroundColor Green
        } else {
            Write-Host "  ✅ Todo tráfego ($($rule.IpProtocol)) - Destino: $($rule.IpRanges[0].CidrIp)" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "✅ Verificação concluída!" -ForegroundColor Green

