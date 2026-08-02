"""
Tests del servicio de notificaciones (services/notification_service.py).

Estaba en 0%. Es la única vía por la que un supervisor se entera de que un
incidente va a vencer, y todos sus fallos son silenciosos por diseño: `_send`
captura cualquier excepción y devuelve False.

Ningún test abre un socket: `smtplib.SMTP` se mockea siempre.
"""

from unittest.mock import MagicMock, patch

import pytest

from services import notification_service


# ==========================================
# Construcción del mensaje
# ==========================================

@pytest.mark.unit
class TestBuildMessage:

    def test_arma_las_cabeceras_basicas(self):
        msg = notification_service._build_message(
            "supervisor@example.com", "Asunto de prueba", "<p>cuerpo</p>"
        )

        assert msg["To"] == "supervisor@example.com"
        assert msg["Subject"] == "Asunto de prueba"
        assert msg["From"] is not None

    def test_el_cuerpo_va_como_html(self):
        msg = notification_service._build_message(
            "a@example.com", "x", "<h2>Alerta</h2>"
        )

        payloads = msg.get_payload()
        assert len(payloads) == 1
        assert payloads[0].get_content_type() == "text/html"
        assert "<h2>Alerta</h2>" in payloads[0].get_payload(decode=True).decode("utf-8")

    def test_soporta_acentos_y_emoji_en_el_cuerpo(self):
        """El texto real de las alertas lleva '⚠️' y palabras acentuadas."""
        msg = notification_service._build_message(
            "a@example.com", "x", "<p>⚠️ Atención: dirección sin señalización</p>"
        )

        decoded = msg.get_payload()[0].get_payload(decode=True).decode("utf-8")
        assert "⚠️" in decoded
        assert "señalización" in decoded


# ==========================================
# _send
# ==========================================

@pytest.mark.unit
class TestSend:

    def test_no_envia_nada_si_smtp_esta_desactivado(self):
        with patch.object(notification_service.settings, "SMTP_ENABLED", False):
            with patch("services.notification_service.smtplib.SMTP") as smtp:
                enviado = notification_service._send("a@example.com", "x", "<p>y</p>")

        assert enviado is False
        smtp.assert_not_called()

    def test_envia_con_starttls_y_login_cuando_esta_activo(self):
        with patch.object(notification_service.settings, "SMTP_ENABLED", True):
            with patch("services.notification_service.smtplib.SMTP") as smtp:
                server = smtp.return_value.__enter__.return_value

                enviado = notification_service._send("a@example.com", "x", "<p>y</p>")

        assert enviado is True
        server.starttls.assert_called_once()
        server.login.assert_called_once()
        server.sendmail.assert_called_once()

    def test_devuelve_false_si_el_servidor_falla(self):
        with patch.object(notification_service.settings, "SMTP_ENABLED", True):
            with patch("services.notification_service.smtplib.SMTP") as smtp:
                smtp.return_value.__enter__.return_value.sendmail.side_effect = OSError(
                    "conexión rechazada"
                )

                enviado = notification_service._send("a@example.com", "x", "<p>y</p>")

        assert enviado is False

    def test_un_fallo_de_envio_nunca_propaga_la_excepcion(self):
        """El job de SLA recorre incidentes en bucle: una excepción lo abortaría entero."""
        with patch.object(notification_service.settings, "SMTP_ENABLED", True):
            with patch("services.notification_service.smtplib.SMTP") as smtp:
                smtp.side_effect = RuntimeError("DNS caído")

                # No debe lanzar
                assert notification_service._send("a@example.com", "x", "<p>y</p>") is False


# ==========================================
# send_sla_warning
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestSendSlaWarning:

    def test_el_asunto_lleva_el_id_y_las_horas_restantes(self):
        with patch("services.notification_service._send", return_value=True) as send:
            notification_service.send_sla_warning(
                to_email="sup@example.com",
                incident_id=77,
                address="Av. Duarte 100",
                priority="alta",
                hours_remaining=3.25,
            )

        asunto = send.call_args.args[1]
        assert "#77" in asunto
        assert "3.2h" in asunto or "3.3h" in asunto

    def test_el_cuerpo_incluye_direccion_y_prioridad(self):
        with patch("services.notification_service._send", return_value=True) as send:
            notification_service.send_sla_warning(
                to_email="sup@example.com",
                incident_id=1,
                address="Calle El Sol 5",
                priority="critica",
                hours_remaining=1.0,
            )

        cuerpo = send.call_args.args[2]
        assert "Calle El Sol 5" in cuerpo
        assert "CRITICA" in cuerpo

    def test_sin_direccion_muestra_un_texto_por_defecto(self):
        with patch("services.notification_service._send", return_value=True) as send:
            notification_service.send_sla_warning(
                to_email="sup@example.com",
                incident_id=1,
                address=None,
                priority="baja",
                hours_remaining=10.0,
            )

        assert "Sin dirección" in send.call_args.args[2]

    def test_propaga_el_resultado_del_envio(self):
        with patch("services.notification_service._send", return_value=False):
            resultado = notification_service.send_sla_warning(
                "sup@example.com", 1, "x", "baja", 1.0
            )

        assert resultado is False


# ==========================================
# send_sla_breach
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestSendSlaBreach:

    def test_el_asunto_marca_el_vencimiento(self):
        with patch("services.notification_service._send", return_value=True) as send:
            notification_service.send_sla_breach(
                to_email="sup@example.com",
                incident_id=99,
                address="Av. Duarte 100",
                priority="alta",
            )

        asunto = send.call_args.args[1]
        assert "#99" in asunto
        assert "VENCIDO" in asunto

    def test_el_cuerpo_pide_escalamiento(self):
        with patch("services.notification_service._send", return_value=True) as send:
            notification_service.send_sla_breach("sup@example.com", 1, None, "critica")

        cuerpo = send.call_args.args[2]
        assert "escalamiento" in cuerpo.lower()
        assert "Sin dirección" in cuerpo
