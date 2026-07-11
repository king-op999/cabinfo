<?php
header("Content-Type: application/json");

$rc = trim($_GET['rc'] ?? '');

if ($rc == '') {
    echo json_encode(["status" => "error", "message" => "No RC number"]);
    exit;
}

$session = uniqid() . "-" . uniqid();

$payload = json_encode([
    "regNo" => $rc,
    "sessionid" => $session
]);

$url = "https://api1.91wheels.com/api/v1/third/rc-detail";

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_HTTPHEADER => [
        "Content-Type: application/json",
        "Accept: application/json, text/plain, */*",
        "Origin: https://www.91wheels.com",
        "Referer: https://www.91wheels.com/",
        "User-Agent: Mozilla/5.0 (Linux; Android 10; Mobile Safari/537.36)"
    ]
]);

$res = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo json_encode(["status" => "error", "message" => $err]);
    exit;
}

echo $res;
?>
