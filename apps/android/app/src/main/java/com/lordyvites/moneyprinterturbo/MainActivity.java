package com.lordyvites.moneyprinterturbo;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.net.URI;

public class MainActivity extends Activity {
    private WebView web;
    private String origin;
    private LinearLayout content;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showConnect();
    }

    private TextView text(String value, int size) {
        TextView view = new TextView(this);
        view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(237,244,231));
        view.setPadding(0,16,0,16); return view;
    }

    private void showConnect() {
        if (web != null) { web.destroy(); web = null; }
        content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(32,48,32,24); content.setBackgroundColor(Color.rgb(20,32,25));
        setContentView(content);
        content.addView(text("LORDYVITES", 28));
        content.addView(text("Your computer. Your creative studio.", 20));
        content.addView(text("1. Open Lordyvites on your Windows PC.\n2. Connect both devices to the same trusted Wi-Fi.\n3. Enter the PC address shown in the Windows app.", 16));
        EditText address = new EditText(this);
        address.setTextColor(Color.WHITE); address.setHintTextColor(Color.LTGRAY);
        address.setSingleLine(true); address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        address.setHint("http://192.168.1.10:8765");
        address.setText(getPreferences(MODE_PRIVATE).getString("pc", ""));
        content.addView(address);
        Button connect = new Button(this); connect.setText("Connect to my computer"); content.addView(connect);
        content.addView(text("You'll be asked for the pairing code shown on your PC. Keep the Windows app open while creating videos.\n\nThis companion does not render videos on your phone. Your PC uses your configured AI and stock-video services.", 14));
        connect.setOnClickListener(view -> {
            String candidate = address.getText().toString().trim();
            if (!candidate.contains("://")) candidate = "http://" + candidate;
            try {
                URI uri = new URI(candidate);
                String host = uri.getHost();
                if (!"http".equals(uri.getScheme()) || !privateIPv4(host) || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null || (uri.getPath() != null && !uri.getPath().isEmpty() && !uri.getPath().equals("/"))) throw new Exception();
                origin = "http://" + host + ":" + (uri.getPort() == -1 ? 8765 : uri.getPort());
                getPreferences(MODE_PRIVATE).edit().putString("pc", origin).apply();
                openStudio();
            } catch (Exception error) {
                new AlertDialog.Builder(this).setMessage("Enter the local PC address from the Windows app, for example http://192.168.1.10:8765").setPositiveButton("OK", null).show();
            }
        });
    }

    private boolean privateIPv4(String host) {
        if (host == null) return false;
        String[] parts = host.split("\\."); if (parts.length != 4) return false;
        try {
            int[] octets = new int[4];
            for (int i=0; i<4; i++) { if (!parts[i].matches("[0-9]{1,3}")) return false; octets[i] = Integer.parseInt(parts[i]); if (octets[i]>255) return false; }
            return octets[0] == 10 || (octets[0] == 192 && octets[1] == 168) || (octets[0] == 172 && octets[1]>=16 && octets[1]<=31);
        } catch (NumberFormatException error) { return false; }
    }

    private boolean sameOrigin(String url) {
        try {
            URI expected = new URI(origin), actual = new URI(url);
            return expected.getScheme().equals(actual.getScheme()) && expected.getHost().equals(actual.getHost()) && expected.getPort() == actual.getPort() && actual.getUserInfo() == null;
        } catch (Exception error) { return false; }
    }

    private void openStudio() {
        LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL);
        Button change = new Button(this); change.setText("Change computer / reconnect"); layout.addView(change);
        change.setOnClickListener(view -> showConnect());
        web = new WebView(this); layout.addView(web, new LinearLayout.LayoutParams(-1,0,1)); setContentView(layout);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false); web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) { return !sameOrigin(request.getUrl().toString()); }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, android.webkit.WebResourceError error) {
                if (request.isForMainFrame()) new AlertDialog.Builder(MainActivity.this).setMessage("Could not reach your PC. Check that the Windows app is running, both devices use the same Wi-Fi, and Windows allows Private network access.").setPositiveButton("Reconnect", (dialog, which) -> showConnect()).show();
            }
        });
        web.setDownloadListener((url, userAgent, disposition, mime, length) -> {
            if (!sameOrigin(url) || !Uri.parse(url).getPath().startsWith("/tasks/")) return;
            try {
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                String cookies = CookieManager.getInstance().getCookie(url);
                if (cookies != null) request.addRequestHeader("Cookie", cookies);
                request.addRequestHeader("User-Agent", userAgent);
                request.setMimeType(mime);
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "Lordyvites-" + System.currentTimeMillis() + ".mp4");
                ((DownloadManager)getSystemService(Context.DOWNLOAD_SERVICE)).enqueue(request);
                Toast.makeText(this, "Saving video to Downloads", Toast.LENGTH_LONG).show();
            } catch (Exception error) { Toast.makeText(this, "Couldn't download. Reconnect and try again.", Toast.LENGTH_LONG).show(); }
        });
        web.loadUrl(origin + "/");
    }

    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack(); else if (web != null) showConnect(); else super.onBackPressed();
    }
    @Override protected void onDestroy() { if (web != null) web.destroy(); super.onDestroy(); }
}
