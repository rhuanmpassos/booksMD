# Script para configurar Cloudflare Tunnel (HTTPS gratuito)
# Execute no servidor EC2 via SSH

$instanceId = "i-08325549fdbee150a"
$publicIp = "52.87.194.234"
$keyPath = "..\booksmd-backend-key.pem"

Write-Host "🔒 Configurando Cloudflare Tunnel para HTTPS gratuito..." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Você precisa ter uma conta no Cloudflare (gratuita)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Passos:" -ForegroundColor Cyan
Write-Host "1. Acesse: https://one.dash.cloudflare.com/" -ForegroundColor Gray
Write-Host "2. Vá em Zero Trust > Networks > Tunnels" -ForegroundColor Gray
Write-Host "3. Clique em 'Create a tunnel'" -ForegroundColor Gray
Write-Host "4. Escolha 'Cloudflared'" -ForegroundColor Gray
Write-Host "5. Dê um nome: booksmd-backend" -ForegroundColor Gray
Write-Host "6. Copie o comando de instalação" -ForegroundColor Gray
Write-Host ""
Write-Host "Ou execute manualmente no servidor:" -ForegroundColor Yellow
Write-Host "ssh -i $keyPath ec2-user@$publicIp" -ForegroundColor Gray
Write-Host ""
Write-Host "No servidor, execute:" -ForegroundColor Yellow
Write-Host "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared" -ForegroundColor Gray
Write-Host "chmod +x /usr/local/bin/cloudflared" -ForegroundColor Gray
Write-Host "cloudflared tunnel login" -ForegroundColor Gray
Write-Host "cloudflared tunnel create booksmd-backend" -ForegroundColor Gray
Write-Host "cloudflared tunnel route dns booksmd-backend api.booksmd.seu-dominio.com" -ForegroundColor Gray
Write-Host "cloudflared tunnel run booksmd-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "Depois configure o arquivo de config:" -ForegroundColor Yellow
Write-Host "nano ~/.cloudflared/config.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "Conteudo:" -ForegroundColor Yellow
Write-Host "tunnel: booksmd-backend" -ForegroundColor Gray
Write-Host "credentials-file: /home/ec2-user/.cloudflared/[tunnel-id].json" -ForegroundColor Gray
Write-Host "" -ForegroundColor Gray
Write-Host "ingress:" -ForegroundColor Gray
Write-Host "  - hostname: api.booksmd.seu-dominio.com" -ForegroundColor Gray
Write-Host "    service: http://localhost:8000" -ForegroundColor Gray
Write-Host "  - service: http_status:404" -ForegroundColor Gray
Write-Host ""

