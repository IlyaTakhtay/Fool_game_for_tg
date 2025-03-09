import React from "react";
import './BeautyForm.css';

function BeautyForm({ children, className = null }) {
    if (className != null){ 
        return (
            <div className={`beauty-form ${className}`}>
            {children}
            </div>
        );
    } else {
        return (
            <div className='beauty-form'>
            {children}
            </div>
        );
    }
}

export default BeautyForm;
