from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from NEMO.models import AreaAccessRecord, Reservation, ScheduledOutage, UsageEvent
from NEMO.utilities import format_datetime


@login_required
@require_GET
def reservation_details(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    popup_view = request.GET.get("popup_view")
    if reservation.cancelled:
        error_message = "This reservation was cancelled by {0} at {1}.".format(
            reservation.cancelled_by, format_datetime(reservation.cancellation_time)
        )
        return HttpResponseNotFound(error_message)
    reservation_project_can_be_changed = (
        (request.user.is_staff or request.user.is_staff_on_tool(reservation.tool) or request.user == reservation.user)
        and reservation.has_not_ended
        and reservation.has_not_started
        and reservation.user.active_project_count() > 1
    )

    # Get authorized users for the tool
    authorized_users = []
    if reservation.tool:
        # Staff users
        staff_users = User.objects.filter(is_active=True, is_staff=True)
        # Tool-specific staff
        tool_staff = reservation.tool.staff.filter(is_active=True)
        # Qualified users
        qualified_users = reservation.tool.user_set.filter(is_active=True)
        # Combine and remove duplicates
        authorized_users = list(set(staff_users) | set(tool_staff) | set(qualified_users))
        authorized_users.sort(key=lambda x: x.get_full_name())

    # Check if invitee can be changed
    reservation_invitee_can_be_changed = (
        reservation.tool and
        reservation.has_not_ended() and 
        reservation.has_not_started() and
        (request.user.is_staff or request.user.is_staff_on_tool(reservation.tool) or request.user == reservation.user)
    )

    template_data = {
        "reservation": reservation,
        "reservation_project_can_be_changed": reservation_project_can_be_changed,
        "authorized_users": authorized_users,
        "reservation_invitee_can_be_changed": reservation_invitee_can_be_changed,
        "popup_view": popup_view,
    }

    return render(request, "event_details/reservation_details.html", template_data)


@login_required
@require_GET
def outage_details(request, outage_id):
    outage = get_object_or_404(ScheduledOutage, id=outage_id)
    return render(
        request, "event_details/outage_details.html", {"outage": outage, "popup_view": request.GET.get("popup_view")}
    )


@login_required
@require_GET
def usage_details(request, event_id):
    event = get_object_or_404(UsageEvent, id=event_id)
    return render(
        request, "event_details/usage_details.html", {"event": event, "popup_view": request.GET.get("popup_view")}
    )


@login_required
@require_GET
def area_access_details(request, event_id):
    event = get_object_or_404(AreaAccessRecord, id=event_id)
    return render(
        request, "event_details/area_access_details.html", {"event": event, "popup_view": request.GET.get("popup_view")}
    )
