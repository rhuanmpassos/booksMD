# Verificar portas do Security Group
$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$region = "us-east-1"
$sgId = "sg-0e3e80528a9e9f2ba"

Write-Host "Verificando Security Group: $sgId" -ForegroundColor Cyan

$result = & $aws ec2 describe-security-groups --group-ids $sgId --region $region --output json | ConvertFrom-Json
$rules = $result.SecurityGroups[0].IpPermissions

Write-Host "`nPortas abertas:" -ForegroundColor Yellow
foreach ($rule in $rules) {
    $port = $rule.FromPort
    $protocol = $rule.IpProtocol
    if ($rule.IpRanges.Count -gt 0) {
        $cidr = $rule.IpRanges[0].CidrIp
        Write-Host "  Porta $port ($protocol) - Origem: $cidr" -ForegroundColor Green
    }
}

# Verificar se porta 8000 está aberta
$port8000 = $rules | Where-Object { $_.FromPort -eq 8000 -and $_.IpProtocol -eq 'tcp' }
if ($port8000) {
    Write-Host "`n✅ Porta 8000 (HTTP) está ABERTA" -ForegroundColor Green
} else {
    Write-Host "`n❌ Porta 8000 (HTTP) NÃO está aberta!" -ForegroundColor Red
    Write-Host "Abrindo porta 8000..." -ForegroundColor Yellow
    & $aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $region
    Write-Host "✅ Porta 8000 aberta!" -ForegroundColor Green
}

