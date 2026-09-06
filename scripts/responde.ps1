Set-Location "C:\Users\D\magi-port\VeniceMAGI"
gh run view 34052672615 --log-failed 2>&1 |
  Select-String -Pattern "FAILED|assert|Error|error:" |
  Select-Object -Last 30
