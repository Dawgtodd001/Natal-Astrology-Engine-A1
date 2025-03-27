/**
 * Geocoding utility functions for the Natal Astrology Engine
 * Converts location names to latitude/longitude coordinates
 */

// Use OpenStreetMap's Nominatim service for geocoding
// This is a free service with usage limits - for production use,
// consider a commercial geocoding service with an API key

/**
 * Get coordinates from a location string using OpenStreetMap's Nominatim API
 * 
 * @param {string} locationString - The location to geocode (e.g., "New York, NY")
 * @param {function} successCallback - Callback function on success, receives lat/lng
 * @param {function} errorCallback - Callback function on error
 */
function geocodeLocation(locationString, successCallback, errorCallback) {
    // Don't attempt geocoding if the input is empty
    if (!locationString || locationString.trim() === '') {
        if (errorCallback) errorCallback('Please enter a location');
        return;
    }
    
    // Show loading state
    const locationField = document.getElementById('location');
    if (locationField) {
        locationField.classList.add('loading');
    }
    
    // Build the Nominatim API URL (format=json to get JSON response)
    const apiUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationString)}&limit=1`;
    
    // Make the API request
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading state
            if (locationField) {
                locationField.classList.remove('loading');
            }
            
            // Check if we have results
            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lng = parseFloat(result.lon);
                const displayName = result.display_name;
                
                // Get the timezone based on coordinates (if we have a separate function for this)
                const timezone = getTimezoneFromCoordinates(lat, lng);
                
                // Call the success callback with the coordinates
                if (successCallback) {
                    successCallback(lat, lng, displayName, timezone);
                }
            } else {
                // No results found
                if (errorCallback) {
                    errorCallback('Location not found. Please try a different search term.');
                }
            }
        })
        .catch(error => {
            // Remove loading state
            if (locationField) {
                locationField.classList.remove('loading');
            }
            
            console.error('Geocoding error:', error);
            
            // Use manual location inputs if geocoding fails
            const errorMsg = 'Geocoding service unavailable. Please enter coordinates manually or use a preset location.';
            
            if (errorCallback) {
                errorCallback(errorMsg);
            }
            
            // Show user-friendly error in the location result field
            const locationResult = document.getElementById('location-result');
            if (locationResult) {
                locationResult.innerHTML = `<span class="text-warning"><i class="fa fa-exclamation-triangle"></i> ${errorMsg}</span>`;
            }
        });
}

/**
 * Attempt to get timezone from coordinates
 * This is a simplified function - for production use, consider a timezone API
 * 
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {string} - Estimated timezone or empty string if unknown
 */
function getTimezoneFromCoordinates(lat, lng) {
    // This is a simplified approach - in reality we should use a timezone API
    // For now, make some basic estimates based on longitude
    
    // Rough timezone estimation based on longitude
    const hourOffset = Math.round(lng / 15);
    
    if (lng > -130 && lng < -65) {
        // North America
        if (lng < -115) return 'America/Los_Angeles';
        if (lng < -100) return 'America/Denver';
        if (lng < -85) return 'America/Chicago';
        return 'America/New_York';
    } else if (lng > -20 && lng < 25) {
        // Europe/Africa
        if (lng < 0) return 'Europe/London';
        if (lng < 15) return 'Europe/Paris';
        return 'Europe/Istanbul';
    } else if (lng > 100 && lng < 150) {
        // Australia/East Asia
        if (lng > 135) return 'Australia/Sydney';
        return 'Asia/Tokyo';
    }
    
    // Default to empty string - we'll let the server resolve it
    return '';
}

/**
 * Update form fields with geocoded location data
 * 
 * @param {string} locationString - The location to geocode
 * @param {boolean} updateTimezone - Whether to update the timezone field
 */
function updateLocationFields(locationString, updateTimezone = true) {
    // Get references to form fields
    const latitudeField = document.getElementById('latitude');
    const longitudeField = document.getElementById('longitude');
    const timezoneField = document.getElementById('timezone');
    const locationResultField = document.getElementById('location-result');
    
    // Only proceed if we have the required fields
    if (!latitudeField || !longitudeField) {
        console.error('Cannot find latitude or longitude fields');
        return;
    }
    
    // Show that we're working on it
    if (locationResultField) {
        locationResultField.innerHTML = '<span class="text-info"><i class="fa fa-spinner fa-spin"></i> Looking up location...</span>';
    }
    
    // Call the geocoding function
    geocodeLocation(
        locationString,
        // Success callback
        (lat, lng, displayName, timezone) => {
            // Update form fields
            latitudeField.value = lat;
            longitudeField.value = lng;
            
            // Update timezone if requested
            if (updateTimezone && timezoneField && timezone) {
                timezoneField.value = timezone;
            }
            
            // Show success message
            if (locationResultField) {
                locationResultField.innerHTML = `<span class="text-success"><i class="fa fa-check"></i> Found: ${displayName}</span>`;
                // Fade out after 5 seconds
                setTimeout(() => {
                    locationResultField.innerHTML = '';
                }, 5000);
            }
        },
        // Error callback
        (errorMessage) => {
            // Show error message
            if (locationResultField) {
                locationResultField.innerHTML = `<span class="text-danger"><i class="fa fa-exclamation-triangle"></i> ${errorMessage}</span>`;
            }
        }
    );
}