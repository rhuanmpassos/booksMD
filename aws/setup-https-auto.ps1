# Script automatizado para configurar HTTPS gratuito via Cloudflare Tunnel
$instanceId = "i-08325549fdbee150a"
$publicIp = "52.87.194.234"
$keyPath = "..\booksmd-backend-key.pem"

Write-Host "🔒 Configurando HTTPS gratuito com Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host ""

# Verifica se cloudflared já está instalado
Write-Host "Verificando se cloudflared está instalado..." -ForegroundColor Yellow
$checkCmd = "which cloudflared || echo 'not-found'"
$result = $checkCmd | ssh -i $keyPath ec2-user@$publicIp

if ($result -match "not-found") {
    Write-Host "Instalando cloudflared..." -ForegroundColor Yellow
    
    $installCmd = @"
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
cloudflared --version
"@
    
    $installCmd | ssh -i $keyPath ec2-user@$publicIp
    Write-Host "✅ cloudflared instalado" -ForegroundColor Green
} else {
    Write-Host "✅ cloudflared já está instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "⚠️  ATENÇÃO: Para completar a configuração, você precisa:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Fazer login no Cloudflare:" -ForegroundColor Cyan
Write-Host "   ssh -i $keyPath ec2-user@$publicIp" -ForegroundColor Gray
Write-Host "   cloudflared tunnel login" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Criar o tunnel:" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel create booksmd-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Obter o Tunnel ID e configurar:" -ForegroundColor Cyan
Write-Host "   mkdir -p ~/.cloudflared" -ForegroundColor Gray
Write-Host "   nano ~/.cloudflared/config.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "   Conteúdo do config.yml:" -ForegroundColor Yellow
Write-Host "   tunnel: booksmd-backend" -ForegroundColor Gray
Write-Host "   credentials-file: /home/ec2-user/.cloudflared/[TUNNEL-ID].json" -ForegroundColor Gray
Write-Host "   " -ForegroundColor Gray
Write-Host "   ingress:" -ForegroundColor Gray
Write-Host "     - hostname: api-booksmd-[seu-id].trycloudflare.com" -ForegroundColor Gray
Write-Host "       service: http://localhost:8000" -ForegroundColor Gray
Write-Host "     - service: http_status:404" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Iniciar o tunnel:" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel run booksmd-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Configurar como serviço (opcional):" -ForegroundColor Cyan
Write-Host "   sudo cloudflared service install" -ForegroundColor Gray
Write-Host "   sudo systemctl start cloudflared" -ForegroundColor Gray
Write-Host "   sudo systemctl enable cloudflared" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Veja SOLUCAO_MIXED_CONTENT.md para instruções detalhadas" -ForegroundColor Green
Write-Host ""

