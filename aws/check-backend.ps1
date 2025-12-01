# Script para verificar se o backend está rodando
$instanceId = "i-08325549fdbee150a"
$publicIp = "52.87.194.234"
$keyPath = "..\booksmd-backend-key.pem"

Write-Host "Verificando status do backend..." -ForegroundColor Cyan

# Verifica se instância está rodando
$aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$status = & $aws ec2 describe-instance-status --instance-ids $instanceId --query 'InstanceStatuses[0].InstanceState.Name' --output text --region us-east-1

Write-Host "Status da instância: $status" -ForegroundColor Yellow

if ($status -eq "running") {
    Write-Host "`nTestando conexão com backend..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://$publicIp:8000/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "✅ Backend respondendo! Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Resposta: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Backend não responde: $_" -ForegroundColor Red
        Write-Host "`nVerificando serviço no servidor..." -ForegroundColor Yellow
        Write-Host "Execute: ssh -i $keyPath ec2-user@$publicIp 'sudo systemctl status booksmd'" -ForegroundColor Gray
        Write-Host "Ou: ssh -i $keyPath ec2-user@$publicIp 'sudo journalctl -u booksmd -n 50'" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  Instância não está rodando!" -ForegroundColor Yellow
}

