# Script PowerShell para corrigir CORS no backend EC2
$instanceId = "i-08325549fdbee150a"
$publicIp = "52.87.194.234"
$keyPath = "..\booksmd-backend-key.pem"

Write-Host "🔧 Corrigindo CORS no backend..." -ForegroundColor Cyan

# Comando SSH para atualizar CORS
$sshCommand = @"
cd /opt/booksmd/backend
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=https://booksmd.vercel.app,https://booksmd.vercel.app/*|' .env
grep CORS_ORIGINS .env
sudo systemctl restart booksmd
sleep 2
sudo systemctl status booksmd --no-pager -l | head -20
"@

Write-Host "Executando comandos no servidor..." -ForegroundColor Yellow
$sshCommand | ssh -i $keyPath ec2-user@$publicIp

Write-Host "`n✅ CORS atualizado!" -ForegroundColor Green
Write-Host "Teste novamente o upload no frontend." -ForegroundColor Yellow

