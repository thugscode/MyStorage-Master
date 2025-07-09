// Security utilities for MyStorage application

const SecurityUtils = {
    // Function to generate SHA-256 hash
    async generateHash(password) {
        // Convert the string to an ArrayBuffer
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        
        // Generate the hash using SubtleCrypto
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        
        // Convert the hash to a hexadecimal string
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
        
        return hashHex;
    },
    
    // Function to verify password against a stored hash
    async verifyPassword(enteredPassword, correctHash) {
        try {
            // Generate hash from the entered password
            const enteredHash = await this.generateHash(enteredPassword);
            
            // Compare the hashes using constant-time comparison to prevent timing attacks
            return this.timingSafeEqual(enteredHash, correctHash);
        } catch (error) {
            console.error("Error verifying password:", error);
            return false;
        }
    },
    
    // Constant-time string comparison to prevent timing attacks
    timingSafeEqual(a, b) {
        if (a.length !== b.length) {
            return false;
        }
        
        let result = 0;
        for (let i = 0; i < a.length; i++) {
            // XOR comparison of each character code
            result |= (a.charCodeAt(i) ^ b.charCodeAt(i));
        }
        
        return result === 0;
    },
    
    // Function to sanitize strings (prevent XSS)
    sanitizeString(input) {
        if (!input) return '';
        
        const temp = document.createElement('div');
        temp.textContent = input;
        return temp.innerHTML;
    }
};
