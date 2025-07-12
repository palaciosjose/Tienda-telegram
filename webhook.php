<?php
// Proxy para bot debug
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');

    // Log para debug
    error_log("📥 Webhook recibido en PHP: " . substr($input, 0, 200));

    $ch = curl_init();
    // ¡ESTA ES LA LÍNEA A CAMBIAR!
    curl_setopt($ch, CURLOPT_URL, 'http://127.0.0.1:8444/webhook.php'); // <-- Cambia '/webhook' a '/webhook.php'
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $input);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        error_log("❌ Error PHP->Bot: $error");
        echo "Error: $error";
    } else {
        error_log("✅ PHP->Bot OK: HTTP $httpCode");
        echo $response;
    }

    http_response_code($httpCode ?: 200);
} else {
    echo '{"status": "PHP Proxy Active"}';
}
?>
